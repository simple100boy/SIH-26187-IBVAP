import cv2
import numpy as np

class NightEnhancer:
    """
    Night-Vision & Low-Light Enhancement Engine.
    Uses CLAHE (Contrast Limited Adaptive Histogram Equalization) in LAB color space,
    Bilateral Noise Filtering, and Thermal Pseudo-Color Palette overlays for border night operations.
    """
    def __init__(self):
        self.clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))

    def enhance_low_light(self, frame: np.ndarray) -> np.ndarray:
        """Enhances low-light cctv footage to maximize visibility."""
        if frame is None:
            return frame

        # Convert to LAB color space
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # Apply CLAHE to L-channel
        cl = self.clahe.apply(l)

        # Merge channels and convert back to BGR
        limg = cv2.merge((cl, a, b))
        enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

        # Apply slight gamma correction
        gamma = 1.3
        invGamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        enhanced = cv2.LUT(enhanced, table)

        return enhanced

    def apply_thermal_palette(self, frame: np.ndarray, palette_name: str = "ironbow") -> np.ndarray:
        """
        Applies a pseudo-thermal infrared colormap overlay for tactical border night view.
        Supported palettes: 'ironbow', 'jet', 'inferno', 'grayscale'.
        """
        if frame is None:
            return frame

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE to grayscale for sharp thermal contrast
        enhanced_gray = self.clahe.apply(gray)

        if palette_name == "jet":
            thermal = cv2.applyColorMap(enhanced_gray, cv2.COLORMAP_JET)
        elif palette_name == "inferno":
            thermal = cv2.applyColorMap(enhanced_gray, cv2.COLORMAP_INFERNO)
        elif palette_name == "ironbow":
            # COLORMAP_COLORCUBE or COLORMAP_HOT simulates Ironbow nicely
            thermal = cv2.applyColorMap(enhanced_gray, cv2.COLORMAP_HOT)
        else:
            thermal = cv2.cvtColor(enhanced_gray, cv2.COLOR_GRAY2BGR)

        return thermal

# Global instance
night_enhancer = NightEnhancer()
