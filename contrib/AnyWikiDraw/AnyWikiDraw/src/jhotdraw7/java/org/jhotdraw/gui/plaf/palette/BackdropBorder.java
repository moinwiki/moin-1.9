/**
 * @(#)BackdropBorder.java
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

import java.awt.Component;
import java.awt.Graphics;
import java.awt.Insets;
import javax.swing.border.Border;

/**
 * BackdropBorder.
 *
 * @author Werner Randelshofer
 * @version $Id: BackdropBorder.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class BackdropBorder implements Border {

    private Border backgroundBorder;
    private Border foregroundBorder;

    public BackdropBorder(Border backgroundBorder) {
        this(null, backgroundBorder);
    }

    public BackdropBorder(Border foregroundBorder, Border backgroundBorder) {
        this.foregroundBorder = foregroundBorder;
        this.backgroundBorder = backgroundBorder;
    }

    public Border getBackdropBorder() {
        return backgroundBorder;
    }

    public void paintBorder(Component c, Graphics g, int x, int y, int width, int height) {
        if (foregroundBorder != null) {
            foregroundBorder.paintBorder(c, g, x, y, width, height);
        }
    }

    public Insets getBorderInsets(Component c) {
        if (foregroundBorder != null) {
            return foregroundBorder.getBorderInsets(c);
        } else {
            return backgroundBorder.getBorderInsets(c);
        }
    }

    public boolean isBorderOpaque() {
        return backgroundBorder.isBorderOpaque();
    }

    public static class UIResource extends BackdropBorder implements javax.swing.plaf.UIResource {

        public UIResource(Border backgroundBorder) {
            this(null, backgroundBorder);
        }

        public UIResource(Border foregroundBorder, Border backgroundBorder) {
            super(foregroundBorder, backgroundBorder);
        }
    }
}
