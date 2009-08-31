/*
 * @(#)PaletteMenuItemUI.java
 *
 * Copyright (c) 1996-2006 by the original authors of JHotDraw
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


import javax.swing.*;
import java.awt.*;

/**
 * PaletteMenuItemUI.
 *
 * @author  Werner Randelshofer
 * @version $Id: PaletteMenuItemUI.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class PaletteMenuItemUI extends javax.swing.plaf.basic.BasicMenuItemUI {
    /** Creates a new instance. */
    public PaletteMenuItemUI() {
    }
    
    protected void installDefaults() {
        super.installDefaults();
        defaultTextIconGap = 0;   // Should be from table
        //menuItem.setBorderPainted(false);
        //menuItem.setBorder(null);
        arrowIcon = null;
        checkIcon = null;
    }
    protected Dimension getPreferredMenuItemSize(JComponent c,
                                                     Icon checkIcon,
                                                     Icon arrowIcon,
                                                     int defaultTextIconGap) {
        JMenuItem b = (JMenuItem) c;
        Icon icon = (Icon) b.getIcon(); 
        if (icon == null) {
            return new Dimension(22, 22);
        }
        return new Dimension(icon.getIconWidth() + 2, icon.getIconHeight() + 2);
    }
    public void paint(Graphics g, JComponent c) {
        JMenuItem b = (JMenuItem) c;

        // Paint background
	paintBackground(g, b, selectionBackground);

        // Paint the icon
        //((Graphics2D) g).setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        Icon icon = (Icon) b.getIcon(); 
        if (icon != null) {
        icon.paintIcon(b, g, 1, 1);
        }
    }
}
