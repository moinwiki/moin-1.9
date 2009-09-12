/*
 * @(#)ArrangeAction.java
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
import org.jhotdraw.gui.*;
import java.awt.event.ActionEvent;
import javax.swing.*;

/**
 * ArrangeAction.
 * <p>
 * FIXME - Register as PropertyChangeListener on Arrangeable.
 *
 * @author Werner Randelshofer
 * @version $Id: ArrangeAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class ArrangeAction extends AbstractAction {
    public final static String VERTICAL_ID = "window.arrangeVertical";
    public final static String HORIZONTAL_ID = "window.arrangeHorizontal";
    public final static String CASCADE_ID = "window.arrangeCascade";
    private Arrangeable arrangeable;
    private Arrangeable.Arrangement arrangement;
    
    /** Creates a new instance. */
    public ArrangeAction(Arrangeable arrangeable, Arrangeable.Arrangement arrangement) {
        this.arrangeable = arrangeable;
        this.arrangement = arrangement;
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
        String labelID;
        switch (arrangement) {
            case VERTICAL : labelID = VERTICAL_ID; break;
            case HORIZONTAL : labelID = HORIZONTAL_ID; break;
            case CASCADE :
            default :
                labelID = CASCADE_ID; break;
        }
        labels.configureAction(this, labelID);
    }
    
    public void actionPerformed(ActionEvent e) {
            arrangeable.setArrangement(arrangement);
    }
}
