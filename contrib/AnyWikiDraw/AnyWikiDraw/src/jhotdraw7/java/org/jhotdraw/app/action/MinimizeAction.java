/*
 * @(#)MinimizeAction.java
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

import org.jhotdraw.util.*;

import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import org.jhotdraw.app.Application;

/**
 * Minimizes the Frame of the current view.
 *
 * @author  Werner Randelshofer
 * @version $Id: MinimizeAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class MinimizeAction extends AbstractViewAction {
    public final static String ID = "window.minimize";

    /** Creates a new instance. */
    public MinimizeAction(Application app) {
        super(app);
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
        labels.configureAction(this, ID);
    }
    
    private JFrame getFrame() {
        return (JFrame) SwingUtilities.getWindowAncestor(
                getActiveView().getComponent()
                );
    }
    public void actionPerformed(ActionEvent evt) {
        JFrame frame = getFrame();
        if (frame != null) {
            frame.setExtendedState(frame.getExtendedState() ^ Frame.ICONIFIED);
        } else {
            Toolkit.getDefaultToolkit().beep();
        }
    }
}
