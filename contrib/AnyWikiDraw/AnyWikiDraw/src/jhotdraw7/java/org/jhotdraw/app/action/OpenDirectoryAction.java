/*
 * @(#)OpenDirectoryAction.java
 * 
 * Copyright (c) 2009 by the original authors of JHotDraw
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

import javax.swing.JFileChooser;
import org.jhotdraw.app.*;
import org.jhotdraw.util.ResourceBundleUtil;

/**
 * OpenDirectoryAction.
 *
 * @author Werner Randelshofer, Staldenmattweg 2, CH-6405 Immensee
 * @version $Id: OpenDirectoryAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class OpenDirectoryAction extends OpenAction {
    public final static String ID = "file.openDirectory";

    /** Creates a new instance. */
    public OpenDirectoryAction(Application app) {
        super(app);
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
        labels.configureAction(this, ID);
    }
    @Override
    protected JFileChooser getFileChooser(View view) {
        return ((DirectoryView) view).getOpenDirectoryChooser();
    }

}
