/*
 * @(#)LoadAction.java
 *
 * Copyright (c) 1996-2009 by the original authors of JHotDraw
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
import javax.swing.*;
import java.io.*;
import org.jhotdraw.app.Application;
import org.jhotdraw.app.View;

/**
 * Loads a file into the current view.
 *
 * @author  Werner Randelshofer
 * @version $Id: LoadAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class LoadAction extends AbstractSaveBeforeAction {
    public final static String ID = "file.load";
    
    /** Creates a new instance. */
    public LoadAction(Application app) {
        super(app);
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
        labels.configureAction(this, "file.open");
    }

    protected JFileChooser getFileChooser(View view) {
        return view.getOpenChooser();
    }
    
    public void doIt(View view) {
        JFileChooser fileChooser = getFileChooser(view);
        if (fileChooser.showOpenDialog(view.getComponent()) == JFileChooser.APPROVE_OPTION) {
            openFile(view, fileChooser);
        } else {
            view.setEnabled(true);
        }
    }
    
    protected void openFile(final View view, JFileChooser fileChooser) {
        final File file = fileChooser.getSelectedFile();
        
        view.setEnabled(false);
        
        // Open the file
        view.execute(new Worker() {
            public Object construct() {
                try {
                    view.read(file);
                    return null;
                } catch (IOException e) {
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
            view.setEnabled(true);
                getApplication().addRecentFile(file);
        } else {
            JSheet.showMessageSheet(view.getComponent(),
                    "<html>"+UIManager.getString("OptionPane.css")+
                    "<b>Couldn't open the file \""+file+"\".</b><br>"+
                    value,
                    JOptionPane.ERROR_MESSAGE, new SheetListener() {
                public void optionSelected(SheetEvent evt) {
                    view.clear();
                    view.setEnabled(true);
                }
            }
            );
        }
    }
}