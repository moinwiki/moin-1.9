/*
 * @(#)OSXDropOnDockAction.java
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

import org.jhotdraw.gui.Worker;
import org.jhotdraw.util.*;
import net.roydesign.event.*;
import java.awt.event.*;
import javax.swing.*;
import java.io.*;
import org.jhotdraw.app.Application;
import org.jhotdraw.app.View;

/**
 * Opens a new view for each file dropped on the dock icon of the application.
 * This action must be registered with net.roydesign.app.Application.
 *
 * @author  Werner Randelshofer
 * @version $Id: OSXDropOnDockAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class OSXDropOnDockAction extends AbstractApplicationAction {
    public final static String ID = "file.drop";
    private JFileChooser fileChooser;
    private int entries;
    
    /** Creates a new instance. */
    public OSXDropOnDockAction(Application app) {
        super(app);
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
        putValue(Action.NAME, "OSX Drop On Dock");
    }
    
    public void actionPerformed(ActionEvent evt) {
        final Application app = getApplication();
        if (evt instanceof ApplicationEvent) {
            final ApplicationEvent ae = (ApplicationEvent) evt;
            final View p = app.createView();
            p.setEnabled(false);
            app.add(p);
            p.execute(new Worker() {
                public Object construct() {
                    try {
                        p.read(ae.getFile());
                        return null;
                    } catch (IOException e) {
                        return e;
                    }
                }
                public void finished(Object value) {
                    if (value == null) {
                        p.setFile(ae.getFile());
                        p.setEnabled(true);
                    } else {
                        app.dispose(p);
                        JOptionPane.showMessageDialog(
                        null,
                        "<html>"+UIManager.getString("OptionPane.css")+
                        "<b>Can't open file "+ae.getFile()+"</b><p>"+
                        value,
                        "",
                        JOptionPane.ERROR_MESSAGE
                        );
                    }
                }
            });
        }
    }
}