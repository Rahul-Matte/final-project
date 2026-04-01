import cv2
import numpy as np

def analyze_image(uploaded_img):
    """
    Analyzes the uploaded image to determine color quality.
    """
    if uploaded_img is None:
        return "No Image"

    # Reset stream pointer to ensure we read from the beginning
    uploaded_img.seek(0)
    
    file_bytes = np.asarray(
        bytearray(uploaded_img.read()),
        dtype=np.uint8
    )

    img = cv2.imdecode(file_bytes, 1)

    if img is None:
        return "Invalid Image"

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Calculate mean of the Saturation channel (approx color intensity)
    # Using channel 1 (Saturation) or 0 (Hue) depending on crop color logic.
    # Original code used channel 1.
    score = hsv[:,:,1].mean()

    if score > 60:
        return "Good Color"
    else:
        return "Poor Color"


def detect_dominant_color(uploaded_img):
    """
    Detects the dominant color family of the image using HSV Hue analysis.
    Returns: 'Red', 'Green', 'Yellow', 'Brown', or 'Unknown'
    """
    if uploaded_img is None:
        return None

    # Reset stream
    uploaded_img.seek(0)
    file_bytes = np.asarray(bytearray(uploaded_img.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)

    if img is None:
        return None

    # Convert to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Calculate mask counts for different colors
    # Hue ranges (OpenCV Hue is 0-179)
    
    # Red: 0-10 and 170-179
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 50, 50])
    upper_red2 = np.array([179, 255, 255])
    
    # Green: 35-85
    lower_green = np.array([35, 50, 50])
    upper_green = np.array([85, 255, 255])
    
    # Yellow: 20-35
    lower_yellow = np.array([20, 50, 50])
    upper_yellow = np.array([35, 255, 255])
    
    # Brown (approx Orange/Red but lower value/sat): 10-20
    # Actually, simplistic brown can be covered under "Orange/Yellow" or "Dark Red"
    # For simplified crop logic: Potato/Onion might fall here.
    
    mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask_red = mask_red1 + mask_red2
    
    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    
    # Count pixels
    red_pixels = cv2.countNonZero(mask_red)
    green_pixels = cv2.countNonZero(mask_green)
    yellow_pixels = cv2.countNonZero(mask_yellow)
    
    total_pixels = img.shape[0] * img.shape[1]
    
    # Threshold (e.g., if >10% of pixels match)
    # Return the max match
    counts = {"Red": red_pixels, "Green": green_pixels, "Yellow": yellow_pixels}
    max_color = max(counts, key=counts.get)
    
    if counts[max_color] > (0.05 * total_pixels): # at least 5% match
        return max_color
        
    return "Unknown"
