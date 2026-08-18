# Accessibility, ethics, privacy, and limitations

## Accessibility

The upload and submission flow is provided through a browser-based Streamlit interface and a FastAPI HTTP API. The UI provides text input and image upload controls in [ui/app.py](../ui/app.py), while the API accepts text submissions and multipart image uploads in [app/api/main.py](../app/api/main.py).

The project does not currently implement additional accessibility features beyond the standard controls provided by the frameworks. The interface has not undergone a formal accessibility audit, so accessibility should be considered a limitation of the current proof of concept.

## Ethics and risk handling

The project is a proof-of-concept phishing and scam assessment tool rather than a production security control. Its results should therefore be treated as an indication rather than definitive proof that content is malicious or legitimate.

The text analysis uses a trained text-classification model to identify suspicious language patterns. For image analysis, the system first uses EasyOCR to extract visible text from the image and then passes the extracted text to the same phishing text classifier. This means the current image analysis focuses on phishing-related text visible in the image rather than performing a dedicated visual phishing classification.

The result model in [app/common/schemas.py](../app/common/schemas.py) includes a caveat, and the worker tasks return an `unclear` result when analysis cannot be completed. The image assessment is also explicitly described as a low-confidence, single-image check.

These limitations are important because a classifier can produce both false positives and false negatives. Users should not rely on the system alone when deciding whether to click a link, provide credentials, transfer money, or disclose personal information.

## Privacy and data handling

For image analysis, the API reads the uploaded image and writes it to a temporary file before placing the file path into the Celery task queue. The worker reads the temporary file for analysis and attempts to delete it in a `finally` block after processing, as implemented in [app/workers/tasks.py](../app/workers/tasks.py).

The reviewed implementation does not store submitted message bodies, image data, or filenames in a database. Text submitted to the text-analysis endpoint is passed to the worker for classification, while image content is temporarily stored as a file for processing.

The similarity guard in [app/api/guards.py](../app/api/guards.py) keeps recent submission information in process memory. For text submissions, it uses the submitted text for similarity comparison. For images, the API calculates a SHA256 hash of the uploaded bytes and uses that value for the similarity check rather than storing the image itself.

The current implementation does not provide a persistent database or long-term storage mechanism for submitted content. However, this should not be interpreted as a complete privacy guarantee because deployment infrastructure, application logs, operating-system temporary storage, and external model services would need to be considered in a real deployment.

## Upload validation behaviour

The image endpoint in [app/api/main.py](../app/api/main.py) performs several validation checks before creating an analysis job:

- The uploaded content type must be `image/png` or `image/jpeg`.
- The declared `Content-Length` is checked against the configured maximum upload size before the body is read.
- The uploaded content is checked again after reading to prevent oversized files from being processed.
- Empty files are rejected.
- A multipart `file` field is required.
- Valid uploads are written to a temporary file and queued for asynchronous analysis.

The existing tests cover supported PNG and JPEG uploads as well as rejected GIF files, incorrect MIME types, oversized files, empty files, and missing file fields.

The upload limit is configurable through `MAX_UPLOAD_BYTES` and defaults to 10 MB.

## Image analysis and OCR behaviour

The image analysis implementation has been changed from the previous ImageNet-style image classification approach.

The current `ImageChecker` in [app/workers/models.py](../app/workers/models.py) uses EasyOCR to extract text from an uploaded image. Text with an OCR confidence below the configured threshold is ignored. The remaining extracted text is combined and passed to the existing `TextClassifier`.

The resulting image score therefore represents the phishing assessment of the **OCR-extracted text**, not a dedicated visual assessment of the image itself.

This approach is more semantically connected to the phishing detection task than using a generic image-classification model. However, it has important limitations: images containing phishing indicators that are purely visual may not be detected, OCR errors can affect classification, and images with little or no readable text cannot be meaningfully assessed by the text classifier.

If no readable text is detected, the image assessment returns an `unclear` result with a neutral score rather than treating the image as legitimate.

## Similarity guard behaviour

The guard in [app/api/guards.py](../app/api/guards.py) is intended to reduce repeated submissions rather than detect phishing.

For text submissions, recent text values are compared using the configured similarity threshold. For image submissions, the API first calculates a SHA256 hash of the image bytes and then passes that hash to the similarity guard.

The guard is stored in a process-local Python dictionary and protected by a threading lock. It is therefore not shared between separate API processes or instances and its state is lost when the process restarts.

The existing tests verify repeated near-identical text submissions, repeated exact-content image submissions, and separation of client strike counts.

## Limitations

### 1. Image analysis is OCR-based rather than visual phishing detection

The current image checker does not use a model trained specifically to classify phishing screenshots or other malicious images.

Instead, it follows this pipeline:

**Image → EasyOCR → extracted text → phishing text classifier → phishing score**

This means the system can identify suspicious wording contained in screenshots, but it may miss phishing indicators represented through purely visual elements such as fake logos, layout manipulation, buttons, forms, or visual impersonation.

### 2. OCR errors can affect the result

OCR may incorrectly recognise, omit, or alter text in an image. Poor image quality, unusual fonts, small text, overlapping elements, or distorted screenshots may therefore reduce classification accuracy.

The OCR confidence threshold also means some detected text may be discarded before classification.

### 3. The text model's score is not a guaranteed probability

The score produced by the text classifier is used as the phishing assessment score, but it should not be interpreted as a mathematically calibrated probability that an input is phishing.

The labels are converted into the project's three result categories:

- `likely_phishing`
- `unclear`
- `likely_legitimate`

The thresholds are defined in [app/workers/tasks.py](../app/workers/tasks.py).

### 4. No real-world evaluation has been performed

The project has not been evaluated against a sufficiently large, representative real-world dataset of phishing messages and screenshots.

Consequently, the current scores should not be treated as evidence of production-level detection accuracy.

A future version should be evaluated using representative phishing and legitimate examples, including screenshots containing different languages, layouts, brands, and types of phishing attacks.

### 5. Similarity protection is process-local

The similarity guard uses in-memory state. It does not persist across restarts and does not share state between multiple API processes or instances.

Although Redis is used by the project's Celery configuration, the current similarity guard itself is not Redis-backed.

A production implementation could move this state to Redis with an appropriate expiration mechanism so that the guard can operate consistently across multiple API instances.

### 6. MIME validation relies on the supplied content type

The API checks the uploaded file's declared MIME type and accepts only `image/png` and `image/jpeg`.

It does not currently inspect the file's magic bytes to independently verify that the file contents match the declared type. Therefore, the MIME check should be considered basic upload validation rather than a complete file-security mechanism.

### 7. External model and dependency considerations

The text classifier and OCR functionality depend on third-party machine-learning libraries and model files. Model loading can require significant memory and CPU resources, particularly when running OCR locally.

The current implementation also assumes that the required models and dependencies are available in the execution environment. A production deployment would need additional resource limits, dependency management, model version control, and monitoring.

## Documentation and scope

The project should be described as a **proof-of-concept phishing and scam assessment system**.

Its current image functionality should specifically be described as **OCR-assisted phishing detection**, rather than general image phishing detection. The system extracts text from an image and applies the existing phishing text classifier to that extracted text.

The similarity guard should also be described as a mechanism for reducing repeated submissions, not as a security mechanism that detects or prevents phishing attacks.

These limitations should be communicated clearly so that users do not interpret the system's output as a guarantee that content is safe or malicious.