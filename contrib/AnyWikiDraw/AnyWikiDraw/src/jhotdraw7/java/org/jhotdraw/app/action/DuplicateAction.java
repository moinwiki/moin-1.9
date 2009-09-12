/*
 * @(#)DuplicateAction.java
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

import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import org.jhotdraw.util.*;
import org.jhotdraw.app.EditableComponent;

/**
 * DuplicateAction.
 *
 * @author Werner Randelshofer.
 * @version $Id: DuplicateAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class DuplicateAction extends AbstractAction {
    public final static String ID = "edit.duplicate";
    
    /** Creates a new instance. */
    public DuplicateAction() {
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
        labels.configureAction(this, ID);
    }
    
    public void actionPerformed(ActionEvent evt) {
        Component focusOwner = KeyboardFocusManager.
                getCurrentKeyboardFocusManager().
                getPermanentFocusOwner();
        if (focusOwner != null) {
            if (focusOwner instanceof EditableComponent) {
                ((EditableComponent) focusOwner).duplicate();
            } else {
                focusOwner.getToolkit().beep();
            }
        }
    }
}
