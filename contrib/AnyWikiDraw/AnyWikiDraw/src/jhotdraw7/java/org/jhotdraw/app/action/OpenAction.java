/*
 * @(#)OpenAction.java
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
import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import java.io.*;
import org.jhotdraw.app.Application;
import org.jhotdraw.app.View;

/**
 * Opens a file in new view, or in the current view, if it is empty.
 *
 * @author  Werner Randelshofer
 * @version $Id: OpenAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class OpenAction extends AbstractApplicationAction {

    public final static String ID = "file.open";

    /** Creates a new instance. */
    public OpenAction(Application app) {
        super(app);
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
        labels.configureAction(this, ID);
    }

    protected JFileChooser getFileChooser(View view) {
        return view.getOpenChooser();
    }

    public void actionPerformed(ActionEvent evt) {
        final Application app = getApplication();
        if (app.isEnabled()) {
            app.setEnabled(false);
            // Search for an empty view
            View emptyView = app.getActiveView();
            if (emptyView == null ||
                    emptyView.getFile() != null ||
                    emptyView.hasUnsavedChanges() ||
                    !emptyView.isEnabled()) {
                emptyView = null;
            }

            final View view;
            boolean disposeView;
            if (emptyView == null) {
                view = app.createView();
                app.add(view);
                disposeView = true;
            } else {
                view = emptyView;
                disposeView = false;
            }
            JFileChooser fileChooser = getFileChooser(view);
            if (fileChooser.showOpenDialog(app.getComponent()) == JFileChooser.APPROVE_OPTION) {
                app.show(view);
                openFile(fileChooser, view);
            } else {
                if (disposeView) {
                    app.dispose(view);
                }
                app.setEnabled(true);
            }
        }
    }

    protected void openFile(JFileChooser fileChooser, final View view) {
        final Application app = getApplication();
        final File file = fileChooser.getSelectedFile();
        app.setEnabled(true);
        view.setEnabled(false);

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
        final Application app = getApplication();
        if (value == null) {
            view.setFile(file);
            view.setEnabled(true);
            Frame w = (Frame) SwingUtilities.getWindowAncestor(view.getComponent());
            if (w != null) {
                w.setExtendedState(w.getExtendedState() & ~Frame.ICONIFIED);
                w.toFront();
            }
            view.getComponent().requestFocus();
            app.addRecentFile(file);
            app.setEnabled(true);
        } else {
            view.setEnabled(true);
            app.setEnabled(true);
            String message;
            if ((value instanceof Throwable) && ((Throwable) value).getMessage() != null) {
                message = ((Throwable) value).getMessage();
                ((Throwable) value).printStackTrace();
            } else if ((value instanceof Throwable)) {
                message = value.toString();
                ((Throwable) value).printStackTrace();
            } else {
                message = value.toString();
            }
            ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
            JSheet.showMessageSheet(view.getComponent(),
                    "<html>" + UIManager.getString("OptionPane.css") +
                    "<b>" + labels.getFormatted("file.open.couldntOpen.message", file.getName()) + "</b><br>" +
                    ((message == null) ? "" : message),
                    JOptionPane.ERROR_MESSAGE);
        }
    }
}
