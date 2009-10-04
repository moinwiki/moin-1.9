/**
 * @(#)ColorListCellRenderer.java
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
package org.jhotdraw.color;

import java.awt.*;
import javax.swing.*;

/**
 * ColorListCellRenderer.
 *
 * @author Werner Randelshofer
 * @version $Id: ColorListCellRenderer.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class ColorListCellRenderer extends DefaultListCellRenderer {

    
    private static class ColorIcon implements Icon {

        private Color color;

        public void setColor(Color newValue) {
            color = newValue;
        }

        public void paintIcon(Component c, Graphics g, int x, int y) {
            if (color != null) {
            g.setColor(new Color(0x333333));
            g.drawRect(x, y, getIconWidth() - 1, getIconHeight() - 1);
            g.setColor(Color.WHITE);
            g.drawRect(x + 1, y + 1, getIconWidth() - 3, getIconHeight() - 3);
                g.setColor(color);
                g.fillRect(x + 2, y + 2, getIconWidth() - 4, getIconHeight() - 4);
            }
        }

        public int getIconWidth() {
            return 24;
        }

        public int getIconHeight() {
            return 18;
        }
    }

    private ColorIcon icon;
    
    public ColorListCellRenderer() {
    icon = new ColorIcon();
    setIcon(icon);
    }

    @Override
    public Component getListCellRendererComponent(
            JList list,
            Object value,
            int index,
            boolean isSelected,
            boolean cellHasFocus) {
        super.getListCellRendererComponent(list, value, index, isSelected, cellHasFocus);
        if (value instanceof CompositeColor) {
            value = ((CompositeColor) value).getColor();
        }
        if (value instanceof Color) {
            Color c = (Color) value;
            icon.setColor(c);
            String text = "000000"+Integer.toHexString(c.getRGB());
            text = '#'+text.substring(text.length() - 6);
            //setText(text);
            setToolTipText(text);
            setText("");
        } else {
            icon.setColor(null);
            setText("");
        }
        setIcon(icon);
        return this;
    }
}
