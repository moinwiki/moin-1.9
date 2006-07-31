/*
 * @(#)PaletteIcon.java 5.1
 *
 */

package CH.ifa.draw.util;

import java.awt.*;

/**
 * A three state icon that can be used in Palettes.
 *
 * @see PaletteButton
 */

public  class PaletteIcon extends Object {

    Image       fNormal;
    Image       fPressed;
    Image       fSelected;
    Dimension   fSize;

    public PaletteIcon(Dimension size, Image normal, Image pressed, Image selected) {
        fSize = size;
        fNormal = normal;
        fPressed = pressed;
        fSelected = selected;
    }

    public Image normal() { return fNormal; }
    public Image pressed() { return fPressed; }
    public Image selected() { return fSelected; }

    public int getWidth() { return fSize.width; }
    public int getHeight() { return fSize.height; }

}
