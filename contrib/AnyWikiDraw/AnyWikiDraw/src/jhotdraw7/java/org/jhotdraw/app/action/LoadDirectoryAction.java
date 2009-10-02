/*
 * @(#)LoadDirectoryAction.java
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
 * Presents a directory chooser to the user and then loads the directory
 * into a {@link org.jhotdraw.app.View}.
 * <p>
 * This action requires that the view implements the
 * {@link org.jhotdraw.app.DirectoryView} interface.
 *
 * <hr>
 * <b>Design Patterns</b>
 *
 * <p><em>Framework</em><br>
 * The interfaces and classes listed below define together the contracts
 * of a smaller framework inside of the JHotDraw framework for document oriented
 * applications.<br>
 * Contract: {@link org.jhotdraw.app.DirectoryView}, {@link LoadDirectoryAction}.
 * <hr>
 *
 * @author Werner Randelshofer, Staldenmattweg 2, CH-6405 Immensee
 * @version $Id: LoadDirectoryAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class LoadDirectoryAction extends LoadAction {
    public final static String ID = "file.loadDirectory";

    /** Creates a new instance. */
    public LoadDirectoryAction(Application app) {
        super(app);
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
        labels.configureAction(this, "file.openDirectory");
    }
    @Override
    protected JFileChooser getFileChooser(View view) {
        return ((DirectoryView) view).getOpenDirectoryChooser();
    }

}
