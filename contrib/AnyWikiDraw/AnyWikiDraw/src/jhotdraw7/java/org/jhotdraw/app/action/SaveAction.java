/*
 * @(#)SaveAction.java
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

import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import java.io.*;
import org.jhotdraw.app.*;
import org.jhotdraw.io.*;
import org.jhotdraw.util.*;
import org.jhotdraw.gui.*;
import org.jhotdraw.gui.event.*;

/**
 * SaveAction.
 *
 * @author  Werner Randelshofer
 * @version $Id: SaveAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class SaveAction extends AbstractViewAction {
    public final static String ID = "file.save";
    private boolean saveAs;
    private Component oldFocusOwner;
    
    /** Creates a new instance. */
    public SaveAction(Application app) {
        this(app, false);
    }
    /** Creates a new instance. */
    public SaveAction(Application app, boolean saveAs) {
        super(app);
        this.saveAs = saveAs;
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
        labels.configureAction(this, ID);
    }
    
    
    public void actionPerformed(ActionEvent evt) {
        final View view = getActiveView();
        if (view.isEnabled()) {
            oldFocusOwner = SwingUtilities.getWindowAncestor(view.getComponent()).getFocusOwner();
            view.setEnabled(false);
            
            File saveToFile;
            if (!saveAs && view.getFile() != null && view.canSaveTo(view.getFile())) {
                saveToFile(view, view.getFile());
            } else {
                JFileChooser fileChooser = view.getSaveChooser();
                
                JSheet.showSaveSheet(fileChooser, view.getComponent(), new SheetListener() {
                    public void optionSelected(final SheetEvent evt) {
                        if (evt.getOption() == JFileChooser.APPROVE_OPTION) {
                            final File file;
                            if (evt.getFileChooser().getFileFilter() instanceof ExtensionFileFilter) {
                                file = ((ExtensionFileFilter) evt.getFileChooser().getFileFilter()).
                                        makeAcceptable(evt.getFileChooser().getSelectedFile());
                            } else {
                                file = evt.getFileChooser().getSelectedFile();
                            }
                            saveToFile(view, file);
                        } else {
                            view.setEnabled(true);
                            if (oldFocusOwner != null) {
                                oldFocusOwner.requestFocus();
                            }
                        }
                    }
                });
            }
        }
    }
    
    protected void saveToFile(final View view, final File file) {
        view.execute(new Worker() {
            public Object construct() {
                try {
                    view.write(file);
                    return null;
                } catch (IOException e) {
                    return e;
                }
            }
            public void finished(Object value) {
                fileSaved(view, file, value);
            }
        });
    }
    /**
     * XXX - Change type of value to Throwable
     *
     * @param value is either null for success or a Throwable on failure.
     */
    protected void fileSaved(final View view, File file, Object value) {
        if (value == null) {
            view.setFile(file);
            view.markChangesAsSaved();
            int multiOpenId = 1;
            for (View p : view.getApplication().views()) {
                if (p != view && p.getFile() != null && p.getFile().equals(file)) {
                    multiOpenId = Math.max(multiOpenId, p.getMultipleOpenId() + 1);
                }
            }
            getApplication().addRecentFile(file);
            view.setMultipleOpenId(multiOpenId);
        } else {
            String message;
            if ((value instanceof Throwable) && ((Throwable) value).getMessage() != null) {
                message = ((Throwable) value).getMessage();
            } else {
                message = value.toString();
            }
            ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
            JSheet.showMessageSheet(getActiveView().getComponent(),
                    "<html>" + UIManager.getString("OptionPane.css") +
                    "<b>" + labels.getFormatted("couldntSave", file.getName()) + "</b><br>" +
                    ((message == null) ? "" : message),
                    JOptionPane.ERROR_MESSAGE);
        }
        view.setEnabled(true);
        SwingUtilities.getWindowAncestor(view.getComponent()).toFront();
        if (oldFocusOwner != null) {
            oldFocusOwner.requestFocus();
        }
    }
}