/*
 * @(#)OpenRecentAction.java
 *
 * Copyright (c) 1996-2008 by the original authors of JHotDraw
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
import org.jhotdraw.gui.event.*;
import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import java.io.*;
import org.jhotdraw.app.Application;
import org.jhotdraw.app.View;

/**
 * OpenRecentAction.
 *
 * @author Werner Randelshofer.
 * @version $Id: OpenRecentAction.java 527 2009-06-07 14:28:19Z rawcoder $
  */
public class OpenRecentAction extends AbstractApplicationAction {

    public final static String ID = "file.openRecent";
    private File file;

    /** Creates a new instance. */
    public OpenRecentAction(Application app, File file) {
        super(app);
        this.file = file;
        putValue(Action.NAME, file.getName());
    }

    public void actionPerformed(ActionEvent evt) {
        final Application app = getApplication();
        if (app.isEnabled()) {
            app.setEnabled(false);
            // Search for an empty view
            View emptyView = app.getActiveView();
            if (emptyView == null ||
                    emptyView.getFile() != null ||
                    emptyView.hasUnsavedChanges()) {
                emptyView = null;
            }

            final View p;
            if (emptyView == null) {
                p = app.createView();
                app.add(p);
                app.show(p);
            } else {
                p = emptyView;
            }
            openFile(p);
        }
    }

    protected void openFile(final View view) {
        final Application app = getApplication();
        app.setEnabled(true);


        // If there is another view with we set the multiple open
        // id of our view to max(multiple open id) + 1.
        int multipleOpenId = 1;
        for (View aView : app.views()) {
            if (aView != view &&
                    aView.getFile() != null &&
                    aView.getFile().equals(file)) {
                multipleOpenId = Math.max(multipleOpenId, aView.getMultipleOpenId() + 1);
            }
        }
        view.setMultipleOpenId(multipleOpenId);
        view.setEnabled(false);
        view.getOpenChooser(); // get open chooser is needed by read method.

        // Open the file
        view.execute(new Worker() {

            public Object construct() {
                try {
                    if (file.exists()) {
                        view.read(file);
                        return null;
                    } else {
                        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
                        return new IOException(labels.getFormatted("file.open.fileDoesNotExist.message", file.getName()));
                    }
                } catch (Throwable e) {
                    return e;
                }
            }

            public void finished(Object value) {
                fileOpened(view, file, value);
            }
        });
    }

    protected void fileOpened(final View view, File file, Object value) {
        if (value == null) {
            view.setFile(file);
            Frame w = (Frame) SwingUtilities.getWindowAncestor(view.getComponent());
            if (w != null) {
                w.setExtendedState(w.getExtendedState() & ~Frame.ICONIFIED);
                w.toFront();
            }
            view.setEnabled(true);
            view.getComponent().requestFocus();
        } else {
            String message = null;
            if (value instanceof Throwable) {
                ((Throwable) value).printStackTrace();
                message = ((Throwable) value).getMessage();
                if (message == null) {
                    message = value.toString();
                }
            }
            ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
            JSheet.showMessageSheet(view.getComponent(),
                    "<html>" + UIManager.getString("OptionPane.css") +
                    "<b>" + labels.getFormatted("file.open.couldntOpen.message", file.getName()) + "</b><br>" +
                    (message == null ? "" : message),
                    JOptionPane.ERROR_MESSAGE, new SheetListener() {

                public void optionSelected(SheetEvent evt) {
                    view.setEnabled(true);
                }
            });
        }
    }
}
