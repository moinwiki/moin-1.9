/*
 * @(#)LoadRecentAction.java
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
import java.awt.*;
import javax.swing.*;
import java.io.*;
import org.jhotdraw.app.Application;
import org.jhotdraw.app.View;

/**
 * LoadRecentAction.
 *
 * @author Werner Randelshofer.
 * @version $Id: LoadRecentAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class LoadRecentAction extends AbstractSaveBeforeAction {
    public final static String ID = "file.loadRecent";
    private File file;
    
    /** Creates a new instance. */
    public LoadRecentAction(Application app, File file) {
        super(app);
        this.file = file;
        putValue(Action.NAME, file.getName());
    }
    
    public void doIt(final View view) {
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
        
        // Open the file
        view.execute(new Worker() {
            public Object construct() {
                try {
                    view.read(file);
                    return null;
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
            if (app != null) {
                app.setEnabled(true);
            }
        } else {
            if (value instanceof Throwable) {
                ((Throwable) value).printStackTrace();
            }
            JSheet.showMessageSheet(view.getComponent(),
                    "<html>"+UIManager.getString("OptionPane.css")+
                    "<b>Couldn't open the file \""+file+"\".</b><br>"+
                    value,
                    JOptionPane.ERROR_MESSAGE, new SheetListener() {
                public void optionSelected(SheetEvent evt) {
                    // app.dispose(view);
                }
            }
            );
        }
    }
}
