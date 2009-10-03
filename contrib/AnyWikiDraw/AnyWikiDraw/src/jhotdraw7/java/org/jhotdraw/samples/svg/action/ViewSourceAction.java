/*
 * @(#)ViewSourceAction.java
 *
 * Copyright (c) 2007-2009 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.jhotdraw.samples.svg.action;

import java.awt.*;
import java.awt.event.*;
import java.io.*;
import java.util.prefs.Preferences;
import org.jhotdraw.app.*;
import org.jhotdraw.app.action.*;
import javax.swing.*;
import org.jhotdraw.samples.svg.*;
import org.jhotdraw.samples.svg.io.*;
import org.jhotdraw.util.ResourceBundleUtil;
import org.jhotdraw.util.prefs.PreferencesUtil;

/**
 * ViewSourceAction.
 *
 * @author Werner Randelshofer
 * @version $Id: ViewSourceAction.java 529 2009-06-08 21:12:23Z rawcoder $
 */
public class ViewSourceAction extends AbstractViewAction {

    public final static String ID = "view.viewSource";
    /**
     * We store the dialog as a client property in the view.
     */
    private final static String DIALOG_CLIENT_PROPERTY = "view.viewSource.dialog";

    /** Creates a new instance. */
    public ViewSourceAction(Application app) {
        super(app);
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.samples.svg.Labels");
        labels.configureAction(this, ID);
    }

    public void actionPerformed(ActionEvent e) {
        final SVGView p = (SVGView) getActiveView();
        SVGOutputFormat format = new SVGOutputFormat();
        format.setPrettyPrint(true);
        ByteArrayOutputStream buf = new ByteArrayOutputStream();
        try {
                format.write(buf, p.getDrawing());
                String source = buf.toString("UTF-8");

            final JDialog dialog;
            if (p.getClientProperty(DIALOG_CLIENT_PROPERTY) == null) {
                dialog = new JDialog((Frame) SwingUtilities.getWindowAncestor(p.getComponent()));
                p.putClientProperty(DIALOG_CLIENT_PROPERTY, dialog);
                dialog.setTitle(p.getTitle());
                dialog.setResizable(true);
                dialog.setDefaultCloseOperation(JDialog.DISPOSE_ON_CLOSE);
                JTextArea ta = new JTextArea(source);
                ta.setWrapStyleWord(true);
                ta.setLineWrap(true);
                JScrollPane sp = new JScrollPane(ta);
                //sp.setHorizontalScrollBarPolicy(JScrollPane.HORIZONTAL_SCROLLBAR_NEVER);
                dialog.getContentPane().add(sp);
                dialog.setSize(400, 400);
                dialog.setLocationByPlatform(true);
            } else {
                dialog = (JDialog) p.getClientProperty(DIALOG_CLIENT_PROPERTY);
                JTextArea ta = (JTextArea) ((JScrollPane) dialog.getContentPane().getComponent(0)).getViewport().getView();
                 ta.setText(source);
            }

            Preferences prefs = PreferencesUtil.userNodeForPackage(getClass());
            PreferencesUtil.installFramePrefsHandler(prefs, "viewSource", dialog);

            dialog.addWindowListener(new WindowAdapter() {

                @Override
                public void windowClosed(WindowEvent evt) {
                    getApplication().removeWindow(dialog);
                    p.putClientProperty(DIALOG_CLIENT_PROPERTY, null);
                }
            });

            getApplication().addWindow(dialog, getActiveView());
            dialog.setVisible(true);
        } catch (IOException ex) {
            ex.printStackTrace();
        }
    }
}
