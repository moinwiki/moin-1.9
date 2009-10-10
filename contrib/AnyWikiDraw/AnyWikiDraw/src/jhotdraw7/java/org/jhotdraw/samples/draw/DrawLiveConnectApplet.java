/*
 * @(#)DrawLiveConnectApplet.java
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

package org.jhotdraw.samples.draw;

import org.jhotdraw.draw.Drawing;
import org.jhotdraw.draw.TextFigure;
import org.jhotdraw.gui.*;

import java.awt.*;
import java.awt.geom.*;
import java.io.*;
import java.net.*;
import javax.swing.*;

import netscape.javascript.JSObject;
import org.jhotdraw.xml.*;

/**
 * DrawLiveConnectApplet. Supports loading and saving of images to JavaScript.
 *
 * @author  wrandels
 * @version $Id: DrawLiveConnectApplet.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class DrawLiveConnectApplet extends JApplet {
    private final static String VERSION = "7.0.8";
    private final static String NAME = "JHotDraw Draw";
    
    /** Initializes the applet DrawApplet */
    public void init() {
        // Set look and feel
        // -----------------
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Throwable e) {
            // Do nothing.
            // If we can't set the desired look and feel, UIManager does
            // automaticaly the right thing for us.
        }
        
        // Display copyright info while we are loading the data
        // ----------------------------------------------------
        Container c = getContentPane();
        c.setLayout(new BoxLayout(c, BoxLayout.Y_AXIS));
        String[] lines = getAppletInfo().split("\n");//Strings.split(getAppletInfo(), '\n');
        for (int i=0; i < lines.length; i++) {
            c.add(new JLabel(lines[i]));
        }
        
        // We load the data using a worker thread
        // --------------------------------------
        new Worker() {
            public Object construct() {
                Object result;
                try {
                    if (getParameter("data") != null && getParameter("data").length() > 0) {
                        NanoXMLDOMInput domi = new NanoXMLDOMInput(new DrawFigureFactory(), new StringReader(getParameter("data")));
                        result = domi.readObject(0);
                    } else if (getParameter("datafile") != null) {
                        InputStream in = null;
                        try {
                            URL url = new URL(getDocumentBase(), getParameter("datafile"));
                            in = url.openConnection().getInputStream();
                            NanoXMLDOMInput domi = new NanoXMLDOMInput(new DrawFigureFactory(), in);
                            result = domi.readObject(0);
                        } finally {
                            if (in != null) in.close();
                        }
                    } else {
                        result = null;
                    }
                } catch (Throwable t) {
                    result = t;
                }
                return result;
            }
            public void finished(Object result) {
                Container c = getContentPane();
                c.setLayout(new BorderLayout());
                c.removeAll();
                
                initComponents();
                if (result != null) {
                    if (result instanceof Drawing) {
                        setDrawing((Drawing) result);
                    } else if (result instanceof Throwable) {
                        getDrawing().add(new TextFigure(result.toString()));
                        ((Throwable) result).printStackTrace();
                    }
                }
                
                boolean isLiveConnect;
                try {
                    Class.forName("netscape.javascript.JSObject");
                    isLiveConnect = true;
                } catch (Throwable t) {
                    isLiveConnect = false;
                }
                loadButton.setEnabled(isLiveConnect && getParameter("dataread") != null);
                saveButton.setEnabled(isLiveConnect && getParameter("datawrite") != null);
                
                if (isLiveConnect) {
                    String methodName = getParameter("dataread");
                    if (methodName.indexOf('(') > 0) {
                        methodName = methodName.substring(0, methodName.indexOf('(') - 1);
                    }
                    JSObject win = JSObject.getWindow(DrawLiveConnectApplet.this);
                    Object data = win.call(methodName, new Object[0]);
                    if (data instanceof String) {
                        setData((String) data);
                    }
                }
                c.validate();
            }
        }.start();
    }
    
    
    private void setDrawing(Drawing d) {
        drawingPanel.setDrawing(d);
    }
    private Drawing getDrawing() {
        return drawingPanel.getDrawing();
    }
    
    
    public void setData(String text) {
        if (text != null && text.length() > 0) {
            StringReader in = new StringReader(text);
            try {
                NanoXMLDOMInput domi = new NanoXMLDOMInput(new DrawFigureFactory(), in);
                setDrawing((Drawing) domi.readObject(0));
            } catch (Throwable e) {
                getDrawing().removeAllChildren();
                TextFigure tf = new TextFigure();
                tf.setText(e.getMessage());
                tf.setBounds(new Point2D.Double(10,10), new Point2D.Double(100,100));
                getDrawing().add(tf);
                e.printStackTrace();
            } finally {
                if (in != null) in.close();
            }
        }
    }
    public String getData() {
        CharArrayWriter out = new CharArrayWriter();
        try {
            NanoXMLDOMOutput domo = new NanoXMLDOMOutput(new DrawFigureFactory());
            domo.writeObject(getDrawing());
            domo.save(out);
        } catch (IOException e) {
            TextFigure tf = new TextFigure();
            tf.setText(e.getMessage());
            tf.setBounds(new Point2D.Double(10,10), new Point2D.Double(100,100));
            getDrawing().add(tf);
            e.printStackTrace();
        } finally {
            if (out != null) out.close();
        }
        return out.toString();
    }
    
    public String[][] getParameterInfo() {
        return new String[][] {
            { "data", "String", "the data to be displayed by this applet." },
            { "datafile", "URL", "an URL to a file containing the data to be displayed by this applet." },
            { "dataread", "function()", "the name of a JavaScript function which can be used to read the data." },
            { "datawrite", "function()", "the name of a JavaScript function which can be used to write the data." }
        };
    }
    public String getAppletInfo() {
        return NAME +
                "\nVersion "+VERSION +
                "\n\nCopyright 1996-2008 (c) by the authors of JHotDraw" +
                "\nThis software is licensed under LGPL or" +
                "\nCreative Commons 3.0 BY";
    }
    /** This method is called from within the init() method to
     * initialize the form.
     * WARNING: Do NOT modify this code. The content of this method is
     * always regenerated by the Form Editor.
     */
    private void initComponents() {//GEN-BEGIN:initComponents
        toolButtonGroup = new javax.swing.ButtonGroup();
        drawingPanel = new org.jhotdraw.samples.draw.DrawingPanel();
        jToolBar1 = new javax.swing.JToolBar();
        loadButton = new javax.swing.JButton();
        saveButton = new javax.swing.JButton();

        FormListener formListener = new FormListener();

        getContentPane().add(drawingPanel, java.awt.BorderLayout.CENTER);

        jToolBar1.setFloatable(false);
        loadButton.setText("Laden");
        loadButton.addActionListener(formListener);

        jToolBar1.add(loadButton);

        saveButton.setText("Speichern");
        saveButton.addActionListener(formListener);

        jToolBar1.add(saveButton);

        getContentPane().add(jToolBar1, java.awt.BorderLayout.SOUTH);

    }

    // Code for dispatching events from components to event handlers.

    private class FormListener implements java.awt.event.ActionListener {
        public void actionPerformed(java.awt.event.ActionEvent evt) {
            if (evt.getSource() == loadButton) {
                DrawLiveConnectApplet.this.load(evt);
            }
            else if (evt.getSource() == saveButton) {
                DrawLiveConnectApplet.this.save(evt);
            }
        }
    }//GEN-END:initComponents
    
    private void save(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_save
        try {
            String methodName = getParameter("datawrite");
            if (methodName.indexOf('(') > 0) {
                methodName = methodName.substring(0, methodName.indexOf('(') - 1);
            }
            JSObject win = JSObject.getWindow(this);
            Object result = win.call(methodName, new Object[] { getData() });
        } catch (Throwable t) {
            TextFigure tf = new TextFigure("Fehler: "+t);
            AffineTransform tx = new AffineTransform();
            tx.translate(10, 20);
            tf.transform(tx);
            getDrawing().add(tf);
        }
    }//GEN-LAST:event_save
    
    private void load(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_load
        try {
            String methodName = getParameter("dataread");
            if (methodName.indexOf('(') > 0) {
                methodName = methodName.substring(0, methodName.indexOf('(') - 1);
            }
            JSObject win = JSObject.getWindow(this);
            Object result = win.call(methodName, new Object[0]);
            if (result instanceof String) {
                setData((String) result);
            }
        } catch (Throwable t) {
            TextFigure tf = new TextFigure("Fehler: "+t);
            AffineTransform tx = new AffineTransform();
            tx.translate(10, 20);
            tf.transform(tx);
            getDrawing().add(tf);
        }
        
    }//GEN-LAST:event_load
    
    
    
    // Variables declaration - do not modify//GEN-BEGIN:variables
    private org.jhotdraw.samples.draw.DrawingPanel drawingPanel;
    private javax.swing.JToolBar jToolBar1;
    private javax.swing.JButton loadButton;
    private javax.swing.JButton saveButton;
    private javax.swing.ButtonGroup toolButtonGroup;
    // End of variables declaration//GEN-END:variables
    
}
