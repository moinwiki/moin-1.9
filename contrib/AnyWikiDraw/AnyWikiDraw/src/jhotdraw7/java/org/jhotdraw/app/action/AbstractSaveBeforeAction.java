/*
 * @(#)AbstractSaveBeforeAction.java
 *
 * Copyright (c) 1996-2007 by the original authors of JHotDraw
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

import org.jhotdraw.io.*;
import org.jhotdraw.gui.*;
import org.jhotdraw.gui.event.*;
import org.jhotdraw.util.*;
import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import java.io.*;
import org.jhotdraw.app.Application;
import org.jhotdraw.app.View;

/**
 * This abstract class can be extended to implement an {@code Action} that asks
 * to save unsaved changes of a {@link org.jhotdraw.app.View} before the
 * the action is performed.
 * <p>
 * If the view has no unsaved changes, method doIt is invoked immediately.
 * If unsaved changes are present, a dialog is shown asking whether the user
 * wants to discard the changes, cancel or save the changes before doing it.
 * If the user chooses to discard the chanegs, toIt is invoked immediately.
 * If the user chooses to cancel, the action is aborted.
 * If the user chooses to save the changes, the view is saved, and doIt
 * is only invoked after the view was successfully saved.
 *
 * @author  Werner Randelshofer
 * @version $Id: AbstractSaveBeforeAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public abstract class AbstractSaveBeforeAction extends AbstractViewAction {

    private Component oldFocusOwner;

    /** Creates a new instance. */
    public AbstractSaveBeforeAction(Application app) {
        super(app);
    }

    public void actionPerformed(ActionEvent evt) {
        final View p = getActiveView();
        if (p.isEnabled()) {
            final ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
            Window wAncestor = SwingUtilities.getWindowAncestor(p.getComponent());
            oldFocusOwner = (wAncestor == null) ? null : wAncestor.getFocusOwner();
            p.setEnabled(false);

            if (p.hasUnsavedChanges()) {
                JOptionPane pane = new JOptionPane(
                        "<html>" + UIManager.getString("OptionPane.css") +
                        labels.getString("file.saveBefore.doYouWantToSave.message"),
                        JOptionPane.WARNING_MESSAGE);
                Object[] options = { //
                    labels.getString("file.saveBefore.saveOption.text"),//
                    labels.getString("file.saveBefore.cancelOption.text"), //
                    labels.getString("file.saveBefore.dontSaveOption.text")//
                };
                pane.setOptions(options);
                pane.setInitialValue(options[0]);
                pane.putClientProperty("Quaqua.OptionPane.destructiveOption", new Integer(2));
                JSheet.showSheet(pane, p.getComponent(), new SheetListener() {

                    public void optionSelected(SheetEvent evt) {
                        Object value = evt.getValue();
                        if (value == null || value.equals(labels.getString("file.saveBefore.cancelOption.text"))) {
                            p.setEnabled(true);
                        } else if (value.equals(labels.getString("file.saveBefore.dontSaveOption.text"))) {
                            doIt(p);
                            p.setEnabled(true);
                        } else if (value.equals(labels.getString("file.saveBefore.saveOption.text"))) {
                            saveChanges(p);
                        }
                    }
                });

            } else {
                doIt(p);
                p.setEnabled(true);
                if (oldFocusOwner != null) {
                    oldFocusOwner.requestFocus();
                }
            }
        }
    }

    protected void saveChanges(final View p) {
        if (p.getFile() == null) {
            JFileChooser fileChooser = p.getSaveChooser();
            //int option = fileChooser.showSaveDialog(this);
            JSheet.showSaveSheet(fileChooser, p.getComponent(), new SheetListener() {

                public void optionSelected(final SheetEvent evt) {
                    if (evt.getOption() == JFileChooser.APPROVE_OPTION) {
                        final File file;
                        if (evt.getFileChooser().getFileFilter() instanceof ExtensionFileFilter) {
                            file = ((ExtensionFileFilter) evt.getFileChooser().getFileFilter()).makeAcceptable(evt.getFileChooser().getSelectedFile());
                        } else {
                            file = evt.getFileChooser().getSelectedFile();
                        }
                        saveToFile(p, file);
                    } else {
                        p.setEnabled(true);
                        if (oldFocusOwner != null) {
                            oldFocusOwner.requestFocus();
                        }
                    }
                }
            });
        } else {
            saveToFile(p, p.getFile());
        }
    }

    protected void saveToFile(final View p, final File file) {
        p.execute(new Worker() {

            public Object construct() {
                try {
                    p.write(file);
                    return null;
                } catch (IOException e) {
                    return e;
                }
            }

            public void finished(Object value) {
                fileSaved(p, file, value);
            }
        });
    }

    protected void fileSaved(View p, File file, Object value) {
        if (value == null) {
            p.setFile(file);
            p.markChangesAsSaved();
            doIt(p);
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
                    "<b>" + labels.getFormatted("file.saveBefore.couldntSave.message", file.getName()) + "</b><br>" +
                    ((message == null) ? "" : message),
                    JOptionPane.ERROR_MESSAGE);
        }
        p.setEnabled(true);
        if (oldFocusOwner != null) {
            oldFocusOwner.requestFocus();
        }
    }

    protected abstract void doIt(View p);
}
