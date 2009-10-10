/*
 * @(#)NetApplet.java
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

package org.jhotdraw.samples.net;

import org.jhotdraw.draw.*;
import org.jhotdraw.draw.action.*;
import org.jhotdraw.gui.*;
import org.jhotdraw.util.*;

import java.awt.*;
import java.awt.geom.*;
import java.awt.event.*;
import java.io.*;
import java.net.*;
import java.util.*;
import javax.swing.*;
import javax.swing.event.*;
import org.jhotdraw.xml.*;
/**
 * NetApplet.
 * 
 * 
 * @author Werner Randelshofer
 * @version $Id: NetApplet.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class NetApplet extends JApplet {
    private final static String NAME = "JHotDraw Net";
    private NetPanel drawingPanel;
    
    /**
     * We override getParameter() to make it work even if we have no Applet
     * context.
     */
     public String getParameter(String name) {
         try {
            return super.getParameter(name);
         } catch (NullPointerException e) {
             return null;
         }
     }    
    protected String getVersion() {
        return NetApplet.class.getPackage().getImplementationVersion();
    }
     
    /**
     * Initializes the applet NetApplet
     */
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
        String[] labels = getAppletInfo().split("\n");//Strings.split(getAppletInfo(), '\n');
        for (int i=0; i < labels.length; i++) {
            c.add(new JLabel((labels[i].length() == 0) ? " " : labels[i]));
        }
        
        // We load the data using a worker thread
        // --------------------------------------
        new Worker() {
            public Object construct() {
                Object result;
                try {
                        System.out.println("getParameter.datafile:"+getParameter("datafile"));
                    if (getParameter("data") != null) {
                        NanoXMLDOMInput domi = new NanoXMLDOMInput(new NetFactory(), new StringReader(getParameter("data")));
                        result = domi.readObject(0);
                    } else if (getParameter("datafile") != null) {
                        InputStream in = null;
                        try {
                            URL url = new URL(getDocumentBase(), getParameter("datafile"));
                            in = url.openConnection().getInputStream();
                            NanoXMLDOMInput domi = new NanoXMLDOMInput(new NetFactory(), in);
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
                if (result instanceof Throwable) {
                    ((Throwable) result).printStackTrace();
                }
                Container c = getContentPane();
                c.setLayout(new BorderLayout());
                c.removeAll();
                c.add(drawingPanel = new NetPanel());
                
                initComponents();
                if (result != null) {
                    if (result instanceof Drawing) {
                        Drawing drawing = (Drawing) result;
                        setDrawing(drawing);
                    } else if (result instanceof Throwable) {
                        getDrawing().add(new TextFigure(result.toString()));
                        ((Throwable) result).printStackTrace();
                    }
                }
                initDrawing(getDrawing());
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
    /**
     * Configure Drawing object to support copy and paste.
     */
    @SuppressWarnings("unchecked")
    private void initDrawing(Drawing d) {
        d.setInputFormats((java.util.List<InputFormat>) Collections.EMPTY_LIST);
        d.setOutputFormats((java.util.List<OutputFormat>) Collections.EMPTY_LIST);

        DOMStorableInputOutputFormat ioFormat = new DOMStorableInputOutputFormat(
                new NetFactory()
                );
        
        d.addInputFormat(ioFormat);
        d.addInputFormat(new ImageInputFormat(new ImageFigure()));
        d.addInputFormat(new TextInputFormat(new TextFigure()));
        
        d.addOutputFormat(ioFormat);
        d.addOutputFormat(new ImageOutputFormat());
    }
    
    
    public void setData(String text) {
        if (text != null && text.length() > 0) {
            StringReader in = new StringReader(text);
            try {
                NanoXMLDOMInput domi = new NanoXMLDOMInput(new NetFactory(), in);
                domi.openElement("Net");
                
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
            NanoXMLDOMOutput domo = new NanoXMLDOMOutput(new NetFactory());
            domo.openElement("Net");
            domo.writeObject(getDrawing());
            domo.closeElement();
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
        };
    }
    public String getAppletInfo() {
        return NAME +
                "\nVersion "+getVersion() +
                "\n\nCopyright 1996-2009 (c) by the original authors of JHotDraw and all its contributors" +
                "\nThis software is licensed under LGPL or" +
                "\nCreative Commons 3.0 BY";
    }
    /** This method is called from within the init() method to
     * initialize the form.
     * WARNING: Do NOT modify this code. The content of this method is
     * always regenerated by the Form Editor.
     */
    // <editor-fold defaultstate="collapsed" desc=" Generated Code ">//GEN-BEGIN:initComponents
    private void initComponents() {
        toolButtonGroup = new javax.swing.ButtonGroup();

    }// </editor-fold>//GEN-END:initComponents
    
    public static void main(String[] args) {
        SwingUtilities.invokeLater(new Runnable() {
            public void run() {
        JFrame f = new JFrame("JHotDraw Net Applet");
        f.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        NetApplet a = new NetApplet();
        f.getContentPane().add(a);
        a.init();
        f.setSize(500,400);
        f.setVisible(true);
        a.start();
        }
            });
    }
    
    
    // Variables declaration - do not modify//GEN-BEGIN:variables
    private javax.swing.ButtonGroup toolButtonGroup;
    // End of variables declaration//GEN-END:variables
    
}
