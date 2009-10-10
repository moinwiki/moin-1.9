/*
 * @(#)FindAction.java
 *
 * Copyright (c) 2005 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and
 * contributors of the JHotDraw project ("the copyright holders").
 * You may not use, copy or modify this software, except in
 * accordance with the license agreement you entered into with
 * the copyright holders. For details see accompanying license terms.
 */

package org.jhotdraw.samples.teddy.action;

import org.jhotdraw.app.*;
import org.jhotdraw.samples.teddy.*;
import org.jhotdraw.util.*;
import java.awt.event.*;
import javax.swing.*;
/**
 * FindAction shows the find dialog.
 *
 * @author Werner Randelshofer
 * @version $Id: FindAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class FindAction extends AbstractAction {
    public final static String ID = org.jhotdraw.app.action.FindAction.ID;
    private FindDialog findDialog;
    private Application app;
    private ResourceBundleUtil labels =
            ResourceBundleUtil.getBundle("org.jhotdraw.samples.teddy.Labels");
    
    /**
     * Creates a new instance.
     */
    public FindAction(Application app) {
        this.app = app;
        labels.configureAction(this, ID);
    }
    
    public void actionPerformed(ActionEvent e) {
        if (findDialog == null) {
            findDialog = new FindDialog(app);
            if (app instanceof DefaultOSXApplication) {
                findDialog.addWindowListener(new WindowAdapter() {
                    @Override public void windowClosing(WindowEvent evt) {
                        if (findDialog != null) {
                            ((DefaultOSXApplication) app).removePalette(findDialog);
                            findDialog.setVisible(false);
                        }
                    }
                });
            }
        }
        findDialog.setVisible(true);
        if (app instanceof DefaultOSXApplication) {
            ((DefaultOSXApplication) app).addPalette(findDialog);
        }
    }
}
