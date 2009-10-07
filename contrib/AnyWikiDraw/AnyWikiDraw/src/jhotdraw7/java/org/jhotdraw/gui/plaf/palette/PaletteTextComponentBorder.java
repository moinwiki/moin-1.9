/**
 * @(#)PaletteTextComponentBorder.java
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

import java.awt.Color;
import java.awt.Component;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.Insets;
import java.awt.geom.Point2D;
import javax.swing.*;
import javax.swing.border.Border;
import javax.swing.plaf.UIResource;
import org.apache.batik.ext.awt.*;

/**
 * PaletteTextComponentBorder.
 *
 * @author Werner Randelshofer
 * @version $Id: PaletteTextComponentBorder.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class PaletteTextComponentBorder implements Border, UIResource {

    private final static float[] enabledStops = new float[]{0f, 0.2f};
    private final static Color[] enabledStopColors = new Color[]{new Color(0xc8c8c8), new Color(0xffffff)};

    public void paintBorder(Component c, Graphics gr, int x, int y, int width, int height) {
        Graphics2D g = (Graphics2D) gr;
        JComponent jc = (JComponent) c;
        int borderColor;
        float[] stops;
        Color[] stopColors;
        if (!c.isEnabled()) {
            borderColor = 0x80a5a5a5;
            stops = enabledStops;
            stopColors = enabledStopColors;
        } else {
            borderColor = 0xffa5a5a5;
            stops = enabledStops;
            stopColors = enabledStopColors;
        }

        String segmentPosition = getSegmentPosition(c);
        if (segmentPosition == "first" || segmentPosition == "middle") {
            width += 1;
        }
        g.setColor(new Color(borderColor, true));
        g.drawRect(x, y, width - 1, height - 1);

        LinearGradientPaint lgp = new LinearGradientPaint(
                new Point2D.Float(x, y), new Point2D.Float(x, y + height - 1),
                stops, stopColors,
                MultipleGradientPaint.REPEAT,
                MultipleGradientPaint.LINEAR_RGB);
        g.setPaint(lgp);
        g.fillRect(x + 1, y + 1, width - 2, height - 2);
    }

    private String getSegmentPosition(Component c) {
        String segmentPosition = null;
        if (c instanceof JComponent) {
        segmentPosition = (String) ((JComponent) c).getClientProperty("Palette.Component.segmentPosition");
        }
        return (segmentPosition == null) ? "only" : segmentPosition;
    }

    public Insets getBorderInsets(Component c) {
        Insets insets;
        String segmentPosition = getSegmentPosition(c);
        if (segmentPosition == "first" ||
                segmentPosition == "middle") {
            insets = new Insets(3, 3, 3, 2);
        } else {
            insets = new Insets(3, 3, 3, 3);
        }
        return insets;
    }

    public boolean isBorderOpaque() {
        return true;
    }
}
