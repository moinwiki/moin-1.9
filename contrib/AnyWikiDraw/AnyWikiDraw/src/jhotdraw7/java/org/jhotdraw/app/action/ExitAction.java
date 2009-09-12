/*
 * @(#)ExitAction.java
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

import org.jhotdraw.gui.*;
import org.jhotdraw.gui.Worker;
import org.jhotdraw.gui.event.*;
import org.jhotdraw.util.*;
import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import java.io.*;
import org.jhotdraw.app.Application;
import org.jhotdraw.app.View;

/**
 * Exits the application after letting the user review all unsaved views.
 *
 * @author  Werner Randelshofer
 * @version $Id: ExitAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class ExitAction extends AbstractApplicationAction {
    public final static String ID = "application.exit";
    private Component oldFocusOwner;
    private View unsavedView;
    
    /** Creates a new instance. */
    public ExitAction(Application app) {
        super(app);
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
        labels.configureAction(this, ID);
    }
    
    public void actionPerformed(ActionEvent evt) {
        final Application app = getApplication();
        if (app.isEnabled()) {
            app.setEnabled(false);
            int unsavedViewsCount = 0;
            View documentToBeReviewed = null;
            for (View p : app.views()) {
                if (p.hasUnsavedChanges()) {
                    if (p.isEnabled()) {
                        documentToBeReviewed = p;
                    }
                    unsavedViewsCount++;
                }
            }
            if (unsavedViewsCount > 0 && documentToBeReviewed == null) {
                // Silently abort, if no view can be reviewed.
                app.setEnabled(true);
                return;
            }
            
            switch (unsavedViewsCount) {
                case 0 : {
                    doExit();
                    break;
                }
                case 1 : {
                    unsavedView = documentToBeReviewed;
                    oldFocusOwner = SwingUtilities.getWindowAncestor(unsavedView.getComponent()).getFocusOwner();
                    unsavedView.setEnabled(false);
                    JOptionPane pane = new JOptionPane(
                            "<html>"+UIManager.getString("OptionPane.css")+
                            "<b>Do you want to save changes to this document "+
                            "before exiting?</b><p>"+
                            "If you don't save, your changes will be lost.",
                            JOptionPane.WARNING_MESSAGE
                            );
                    Object[] options = { "Save", "Cancel", "Don't Save" };
                    pane.setOptions(options);
                    pane.setInitialValue(options[0]);
                    pane.putClientProperty("Quaqua.OptionPane.destructiveOption", new Integer(2));
                    JSheet.showSheet(pane, unsavedView.getComponent(), new SheetListener() {
                        public void optionSelected(SheetEvent evt) {
                            Object value = evt.getValue();
                            if (value == null || value.equals("Cancel")) {
                                unsavedView.setEnabled(true);
                                app.setEnabled(true);
                            } else if (value.equals("Don't Save")) {
                                doExit();
                                unsavedView.setEnabled(true);
                            } else if (value.equals("Save")) {
                                saveChanges();
                            }
                        }
                    });
                    
                    break;
                }
                default : {
                    JOptionPane pane = new JOptionPane(
                            "<html>"+UIManager.get("OptionPane.css")+
                            "<b>You have "+unsavedViewsCount+" documents with unsaved changes. "+
                            "Do you want to "+
                            "review these changes before quitting?</b><p>"+
                            "If you don't review your documents, "+
                            "all your changes will be lost.",
                            JOptionPane.QUESTION_MESSAGE
                            );
                    Object[] options = {
                        "Review Changes", "Cancel", "Discard Changes"
                    };
                    pane.setOptions(options);
                    pane.setInitialValue(options[0]);
                    pane.putClientProperty(
                            "Quaqua.OptionPane.destructiveOption", new Integer(2)
                            );
                    JDialog dialog = pane.createDialog(app.getComponent(), null);
                    dialog.setVisible(true);
                    Object value = pane.getValue();
                    if (value == null || value.equals("Cancel")) {
                        app.setEnabled(true);
                    } else if (value.equals("Discard Changes")) {
                        doExit();
                        app.setEnabled(true);
                    } else if (value.equals("Review Changes")) {
                        unsavedView = documentToBeReviewed;
                        reviewChanges();
                    }
                }
            }
        }
    }
    
    protected void saveChanges() {
        if (unsavedView.getFile() == null) {
            JFileChooser fileChooser = unsavedView.getSaveChooser();
            //int option = fileChooser.showSaveDialog(this);
            JSheet.showSaveSheet(fileChooser, unsavedView.getComponent(), new SheetListener() {
                public void optionSelected(final SheetEvent evt) {
                    if (evt.getOption() == JFileChooser.APPROVE_OPTION) {
                        final File file = evt.getFileChooser().getSelectedFile();
                        saveToFile(file);
                    } else {
                        unsavedView.setEnabled(true);
                        if (oldFocusOwner != null) {
                            oldFocusOwner.requestFocus();
                        }
                        getApplication().setEnabled(true);
                    }
                }
            });
        } else {
            saveToFile(unsavedView.getFile());
        }
    }
    
    protected void reviewChanges() {
        if (unsavedView.isEnabled()) {
            oldFocusOwner = SwingUtilities.getWindowAncestor(unsavedView.getComponent()).getFocusOwner();
            unsavedView.setEnabled(false);
            JOptionPane pane = new JOptionPane(
                    "<html>"+UIManager.getString("OptionPane.css")+
                    "<b>Do you want to save changes to this document "+
                    "before exiting?</b><p>"+
                    "If you don't save, your changes will be lost.",
                    JOptionPane.WARNING_MESSAGE
                    );
            Object[] options = { "Save", "Cancel", "Don't Save" };
            pane.setOptions(options);
            pane.setInitialValue(options[0]);
            pane.putClientProperty("Quaqua.OptionPane.destructiveOption", new Integer(2));
            JSheet.showSheet(pane, unsavedView.getComponent(), new SheetListener() {
                public void optionSelected(SheetEvent evt) {
                    Object value = evt.getValue();
                    if (value == null || value.equals("Cancel")) {
                        unsavedView.setEnabled(true);
                        getApplication().setEnabled(true);
                    } else if (value.equals("Don't Save")) {
                        getApplication().dispose(unsavedView);
                        reviewNext();
                    } else if (value.equals("Save")) {
                        saveChangesAndReviewNext();
                    }
                }
            });
        } else {
            getApplication().setEnabled(true);
            System.out.println("review silently aborted");
        }
    }
    
    
    
    protected void saveChangesAndReviewNext() {
        if (unsavedView.getFile() == null) {
            JFileChooser fileChooser = unsavedView.getSaveChooser();
            //int option = fileChooser.showSaveDialog(this);
            JSheet.showSaveSheet(fileChooser, unsavedView.getComponent(), new SheetListener() {
                public void optionSelected(final SheetEvent evt) {
                    if (evt.getOption() == JFileChooser.APPROVE_OPTION) {
                        final File file = evt.getFileChooser().getSelectedFile();
                        saveToFileAndReviewNext(file);
                    } else {
                        unsavedView.setEnabled(true);
                        if (oldFocusOwner != null) {
                            oldFocusOwner.requestFocus();
                        }
                        getApplication().setEnabled(true);
                    }
                }
            });
        } else {
            saveToFileAndReviewNext(unsavedView.getFile());
        }
    }
    
    protected void reviewNext() {
        int unsavedViewsCount = 0;
        View documentToBeReviewed = null;
        for (View p : getApplication().views()) {
            if (p.hasUnsavedChanges()) {
                if (p.isEnabled()) {
                    documentToBeReviewed = p;
                }
                unsavedViewsCount++;
            }
        }
        if (unsavedViewsCount == 0) {
            doExit();
        } else if (documentToBeReviewed != null) {
            unsavedView = documentToBeReviewed;
            reviewChanges();
        } else {
            getApplication().setEnabled(true);
            //System.out.println("exit silently aborted");
        }
    }
    
    protected void saveToFile(final File file) {
        unsavedView.execute(new Worker() {
            public Object construct() {
                try {
                    unsavedView.write(file);
                    return null;
                } catch (IOException e) {
                    return e;
                }
            }
            public void finished(Object value) {
                fileSaved(unsavedView, file, value);
            }
        });
    }
    protected void saveToFileAndReviewNext(final File file) {
        unsavedView.execute(new Worker() {
            public Object construct() {
                try {
                    unsavedView.write(file);
                    return null;
                } catch (IOException e) {
                    return e;
                }
            }
            public void finished(Object value) {
                fileSavedAndReviewNext(unsavedView, file, value);
            }
        });
    }
    
    protected void fileSaved(View unsavedView, File file, Object value) {
        if (value == null) {
            unsavedView.setFile(file);
            doExit();
        } else {
            JSheet.showMessageSheet(unsavedView.getComponent(),
                    "<html>"+UIManager.getString("OptionPane.css")+
                    "<b>Couldn't save to the file \""+file+"\".<p>"+
                    "Reason: "+value,
                    JOptionPane.ERROR_MESSAGE
                    );
        }
        unsavedView.setEnabled(true);
        if (oldFocusOwner != null) {
            oldFocusOwner.requestFocus();
        }
        getApplication().setEnabled(true);
    }
    protected void fileSavedAndReviewNext(View unsavedView, File file, Object value) {
        if (value == null) {
            unsavedView.setFile(file);
            getApplication().dispose(unsavedView);
            reviewNext();
            return;
        } else {
            JSheet.showMessageSheet(unsavedView.getComponent(),
                    "<html>"+UIManager.getString("OptionPane.css")+
                    "<b>Couldn't save to the file \""+file+"\".<p>"+
                    "Reason: "+value,
                    JOptionPane.ERROR_MESSAGE
                    );
        }
        unsavedView.setEnabled(true);
        if (oldFocusOwner != null) {
            oldFocusOwner.requestFocus();
        }
        getApplication().setEnabled(true);
    }
    
    protected void doExit() {
        getApplication().stop();
        System.exit(0);
    }
}
