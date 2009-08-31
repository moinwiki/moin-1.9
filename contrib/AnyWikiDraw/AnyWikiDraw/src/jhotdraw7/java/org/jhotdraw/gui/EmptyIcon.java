/**
 * @(#)EmptyIcon.java
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

package org.jhotdraw.gui;

import java.awt.Component;
import java.awt.Graphics;
import javax.swing.Icon;

/**
 * EmptyIcon.
 *
 * @author Werner Randelshofer
 * @version $Id: EmptyIcon.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class EmptyIcon implements Icon {
    private int width;
    private int height;
    
    public EmptyIcon(int width, int height) {
        this.width = width;
        this.height = height;
    }

    public void paintIcon(Component c, Graphics g, int x, int y) {
    }

    public int getIconWidth() {
        return width;
    }

    public int getIconHeight() {
        return height;
    }

}
