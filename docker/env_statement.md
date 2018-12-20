## These 8 environment vars will be compatible for different applications.
### 1. DEEP_ANALYSIS_MODE
- Enables waitqueue.
- When it's still working on a image for detecting faces, other coming images will be put in the waitqueue without distracting the current process. 

### 2. SAMPLING_TO_SAVE_ENERGY_MODE (compatible for gate)
- Enables Sample Analysis.
- Calculate one image at one time, others will be waited until the current one finishes.

### 3. RESTRICT_RECOGNITON_MODE (compatible for ticketgate)
- Enables only-front calculation.
- filter out non-front faces to improve efficiency

### 4. MINIMAL_FACE_RESOLUTION
- Value of minimal face's resolution
- only faces greater than this value will not be calculated for embedding.

### 5. RECOGNITION_ENSURE_VALUE -- Deprecated
- This value will be deprecated
- used to be a guarantee for recognition in a period time

### 6. BIGGEST_FACE_ONLY_MODE (compatible for ticketgate)
- Enables only-biggest-face calculation
- Only calculate the biggest face in an image, which speed up the process and will not be distracted by others faces.

### 7. UPLOAD_IMAGE_SERVICE_ENABLED (compatible for education system)
- Enable external image uploading for recognition
- Others can upload images to SharpAI system 
