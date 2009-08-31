/*
 * @(#)ExportAction.java
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
import org.jhotdraw.gui.event.*;
import org.jhotdraw.util.*;
import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import java.io.*;
import org.jhotdraw.app.*;

/**
 * Presents a file chooser to the user and then exports the 
 * {@link org.jhotdraw.app.View} to the chosen file.
 * <p>
 * This action requires that the view implements the 
 * {@link org.jhotdraw.app.ExportableView} interface.
 *
 * <hr>
 * <b>Design Patterns</b>
 *
 * <p><em>Framework</em><br>
 * The interfaces and classes listed below define together the contracts
 * of a smaller framework inside of the JHotDraw framework for document oriented
 * applications.<br>
 * Contract: {@link org.jhotdraw.app.ExportableView}, {@link org.jhotdraw.app.action.ExportAction}.
 * <hr>
 *
 * @author Werner Randelshofer
 * @version $Id: ExportAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class ExportAction extends AbstractViewAction {
    public final static String ID = "file.export";
    private Component oldFocusOwner;
    
    /** Creates a new instance. */
    public ExportAction(Application app) {
        super(app);
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
        labels.configureAction(this, ID);
    }
    
    
    public void actionPerformed(ActionEvent evt) {
        final ExportableView view = (ExportableView) getActiveView();
        if (view.isEnabled()) {
            ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
            
            oldFocusOwner = SwingUtilities.getWindowAncestor(view.getComponent()).getFocusOwner();
            view.setEnabled(false);
            
            File saveToFile;
            JFileChooser fileChooser = view.getExportChooser();
            
            JSheet.showSheet(fileChooser, view.getComponent(), labels.getString("filechooser.export"), new SheetListener() {
                public void optionSelected(final SheetEvent evt) {
                    if (evt.getOption() == JFileChooser.APPROVE_OPTION) {
                        final File file = evt.getFileChooser().getSelectedFile();
                        exportToFile(view, file, evt.getFileChooser().getFileFilter(), evt.getFileChooser().getAccessory()
                                
                                );
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
    
    protected void exportToFile(final ExportableView view, final File file,
            final javax.swing.filechooser.FileFilter filter,
            final Component accessory) {
        view.execute(new Worker() {
            public Object construct() {
                try {
                    view.export(file, filter, accessory);
                    return null;
                } catch (Throwable e) {
                    return e;
                }
            }
            public void finished(Object value) {
                fileExported(view, file, value);
            }
        });
    }
    protected void fileExported(ExportableView view, File file, Object value) {
        if (value != null) {
            System.out.flush();
            ((Throwable) value).printStackTrace();
            // FIXME localize this error messsage
            JSheet.showMessageSheet(view.getComponent(),
                    "<html>"+UIManager.getString("OptionPane.css")+
                    "<b>Couldn't export to the file \""+file+"\".<p>"+
                    "Reason: "+value,
                    JOptionPane.ERROR_MESSAGE
                    );
        }
        view.setEnabled(true);
        SwingUtilities.getWindowAncestor(view.getComponent()).toFront();
        if (oldFocusOwner != null) {
            oldFocusOwner.requestFocus();
        }
    }
}