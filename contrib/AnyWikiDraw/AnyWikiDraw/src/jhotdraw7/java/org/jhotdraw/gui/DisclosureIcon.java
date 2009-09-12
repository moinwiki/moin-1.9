/**
 * @(#)DisclosureIcon.java
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

import java.awt.*;
import javax.swing.*;

/**
 * DisclosureIcon.
 *
 * @author Werner Randelshofer
 * @version $Id: DisclosureIcon.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class DisclosureIcon implements Icon {
    /**
     * This client property needs to be set on the component.
     * The value must be a positive Integer. 
     */
    public final static String STATE_COUNT_PROPERTY = "DisclosureIcon.numberOfStates";
    /**
     * This client property needs to be set on the component.
     * The value must be a positive Integer. 
     */
    public final static String CURRENT_STATE_PROPERTY = "DisclosureIcon.currentState";

    public void paintIcon(Component component, Graphics g, int x, int y) {
        JComponent c = (JComponent) component;
        
        int nbOfStates = (c.getClientProperty(STATE_COUNT_PROPERTY) instanceof Integer) ?
        (Integer) c.getClientProperty(STATE_COUNT_PROPERTY) : 2;
        
        int currentState = (c.getClientProperty(CURRENT_STATE_PROPERTY) instanceof Integer) ?
        (Integer) c.getClientProperty(CURRENT_STATE_PROPERTY) : 1;
        
        g.setColor(Color.black);
        g.drawRect(x, y, getIconWidth() - 1, getIconHeight() - 1);
        g.setColor(new Color(0x666666));
        g.fillRect(x + 1, y + 1, 
                1 + (getIconWidth() - 3) * currentState / (nbOfStates - 1), 
                getIconHeight() - 2
                );
    }

    public int getIconWidth() {
        return 10;
    }

    public int getIconHeight() {
       return 8;
    }

}
