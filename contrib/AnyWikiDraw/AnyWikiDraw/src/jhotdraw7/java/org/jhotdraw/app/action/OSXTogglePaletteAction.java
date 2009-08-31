/*
 * @(#)OSXTogglePaletteAction.java
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

package org.jhotdraw.app.action;

import java.awt.event.*;
import javax.swing.*;
import java.awt.*;
import org.jhotdraw.app.DefaultOSXApplication;

/**
 * OSXTogglePaletteAction.
 * 
 * @author Werner Randelshofer.
 * @version $Id: OSXTogglePaletteAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class OSXTogglePaletteAction extends AbstractAction {
    private Window palette;
    private DefaultOSXApplication app;
    private WindowListener windowHandler;
    
    /** Creates a new instance. */
    public OSXTogglePaletteAction(DefaultOSXApplication app, Window palette, String label) {
        super(label);
        this.app = app;
        
        windowHandler = new WindowAdapter() {
            public void windowClosing(WindowEvent evt) {
                putValue(Actions.SELECTED_KEY, false);
            }
        };
        
        setPalette(palette);
        putValue(Actions.SELECTED_KEY, true);
    }
    
    public void putValue(String key, Object newValue) {
        super.putValue(key, newValue);
        if (key == Actions.SELECTED_KEY) {
            if (palette != null) {
                boolean b = (Boolean) newValue;
                if (b) {
                    app.addPalette(palette);
                    palette.setVisible(true);
                } else {
                    app.removePalette(palette);
                    palette.setVisible(false);
                }
            }
        }
    }
    
    public void setPalette(Window newValue) {
        if (palette != null) {
            palette.removeWindowListener(windowHandler);
        }
        
        palette = newValue;
        
        if (palette != null) {
            palette.addWindowListener(windowHandler);
            if (getValue(Actions.SELECTED_KEY) == Boolean.TRUE) {
                app.addPalette(palette);
                palette.setVisible(true);
            } else {
                app.removePalette(palette);
                palette.setVisible(false);
            }
        }
    }
    
    public void actionPerformed(ActionEvent e) {
        if (palette != null) {
            putValue(Actions.SELECTED_KEY, ! palette.isVisible());
        }
    }
}
