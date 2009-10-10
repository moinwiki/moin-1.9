/*
 * @(#)SaveAsAction.java
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
import org.jhotdraw.app.Application;

/**
 * SaveAsAction.
 *
 * @author  Werner Randelshofer
 * @version $Id: SaveAsAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class SaveAsAction extends SaveAction {
    public final static String ID = "file.saveAs";

    /** Creates a new instance. */
    public SaveAsAction(Application app) {
        super(app, true);
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
        labels.configureAction(this, ID);
    }
}