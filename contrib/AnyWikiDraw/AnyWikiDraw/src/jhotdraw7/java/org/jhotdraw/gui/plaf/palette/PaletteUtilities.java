/**
 * @(#)PaletteUtilities.java
 *
 * Copyright (c) 2008 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.jhotdraw.gui.plaf.palette;

import java.awt.*;
import javax.swing.plaf.basic.BasicGraphicsUtils;

/**
 * PaletteUtilities.
 *
 * @author Werner Randelshofer
 * @version $Id: PaletteUtilities.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class PaletteUtilities  extends BasicGraphicsUtils {

    public static final Object beginGraphics(Graphics2D graphics2d) {
        Object object = graphics2d.getRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING);

        /*
        AffineTransform tx = graphics2d.getTransform();
        AffineTransform savedTransform = (AffineTransform) tx.clone();
        tx.scale(0.9,0.9);
        graphics2d.setTransform(tx);
         */
        graphics2d.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING,
                RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
        /*graphics2d.setRenderingHint(RenderingHints.KEY_FRACTIONALMETRICS,
        RenderingHints.VALUE_FRACTIONALMETRICS_ON);*/

        //if (true) return savedTransform;
        return object;
    }

    public static final void endGraphics(Graphics2D graphics2d, Object oldHints) {
        /*
        if (true) {
        graphics2d.setTransform((AffineTransform) oldHints);
        return;
        }*/

        if (oldHints != null) {
            graphics2d.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING,
                    oldHints);
        }
    }

    /**
     * Draw a string with the graphics <code>g</code> at location
     * (<code>x</code>, <code>y</code>)
     * just like <code>g.drawString</code> would.
     * The character at index <code>underlinedIndex</code>
     * in text will be underlined. If <code>index</code> is beyond the
     * bounds of <code>text</code> (including < 0), nothing will be
     * underlined.
     *
     * @param g Graphics to draw with
     * @param text String to draw
     * @param underlinedIndex Index of character in text to underline
     * @param x x coordinate to draw at
     * @param y y coordinate to draw at
     * @since 1.4
     */
    public static void drawStringUnderlineCharAt(Graphics g, String text,
            int underlinedIndex, int x, int y) {
        g.drawString(text, x, y);
        if (underlinedIndex >= 0 && underlinedIndex < text.length()) {
            FontMetrics fm = g.getFontMetrics();
            int underlineRectX = x + fm.stringWidth(text.substring(0, underlinedIndex));
            int underlineRectY = y;
            int underlineRectWidth = fm.charWidth(text.charAt(underlinedIndex));
            int underlineRectHeight = 1;
            g.fillRect(underlineRectX, underlineRectY + fm.getDescent() - 1,
                    underlineRectWidth, underlineRectHeight);
        }
    }
}
