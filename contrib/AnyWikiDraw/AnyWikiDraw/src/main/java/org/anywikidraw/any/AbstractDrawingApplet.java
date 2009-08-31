/*
 * @(#)AbstractDrawingApplet.java
 *
 * Copyright (c) 2006-2008 by the original authors of AnyWikiDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the AnyWikiDraw project ("the copyright holders").
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.anywikidraw.any;

import org.anywikidraw.any.io.HtmlForm;
import org.jhotdraw.io.BoundedRangeInputStream;
import org.anywikidraw.any.io.HttpRequest;
import java.applet.AppletContext;
import org.jhotdraw.draw.*;
import org.jhotdraw.gui.*;
import org.jhotdraw.util.*;

import java.awt.*;
import java.awt.geom.*;
import java.awt.event.*;
import java.io.*;
import java.net.*;
import java.util.*;
import javax.swing.*;
import javax.swing.border.LineBorder;
import org.anywikidraw.any.io.*;
import org.jhotdraw.samples.svg.figures.*;
import org.jhotdraw.samples.svg.io.*;
import org.jhotdraw.samples.svg.gui.*;

/**
 * This is the base class for concrete implementations of SVG drawing
 * applets.
 * <p>
 * The base class loads and saves drawings asynchronously and handles
 * errors. The actual data transmission and the editing of drawings
 * is the responsibility of the subclasses.
 * <p>
 * FIXME - Applet must offer to save file locally, if uploading to server
 * failed.
 * <p>
 * FIXME - Applet must save changes locally and reload them, if the user
 * navigated out of the page and back again, without saving the changes.
 * 
 * @author Werner Randelshofer
 * @version $Id: AbstractDrawingApplet.java 118 2009-06-27 11:07:27Z rawcoder $
 */
public abstract class AbstractDrawingApplet extends JApplet {

    private DrawingComponent drawingComponent;
    /**
     * Lazily initialized in method getVersion();
     */
    private String version;
    private long start;

    public AbstractDrawingApplet() {
        setBackground(Color.WHITE);
        start = System.currentTimeMillis();
    //ResourceBundleUtil.setVerbose(true);
    }

    /**
     * Same as <code>Applet.getParameter()</code> but doesn't throw a
     * NullPointerException when used without an Applet context.
     */
    @Override
    public String getParameter(String name) {
        try {
            return super.getParameter(name);
        } catch (NullPointerException e) {
            return null;
        }
    }

    /**
     * Same as <code>Applet.getDocumentBase()</code> but doesn't throw a
     * NullPointerException when used without an Applet context.
     */
    @Override
    public URL getDocumentBase() {
        try {
            return super.getDocumentBase();
        } catch (NullPointerException e) {
            return null;
        }
    }

    /**
     * Same as <code>Applet.getParameter()</code> but doesn't throw a
     * NullPointerException when used without an Applet context.
     */
    public String getParameter(String name, String defaultValue) {
        try {
            String value = super.getParameter(name);
            return (value == null) ? defaultValue : value;
        } catch (NullPointerException e) {
            return defaultValue;
        }
    }

    /**
     * Displays a progress indicator and then invokes <code>loadDrawing</code>
     * on a worker thread. Displays the drawing panel when finished successfully.
     * Displays an error message when finished unsuccessfully.
     *
     * @see #loadDrawing
     */
    @Override
    public final void init() {
        // set the language of the applet
        if (getParameter("Locale") != null) {
            Locale.setDefault(new Locale(getParameter("Locale")));
        }


        final ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.samples.svg.Labels");

        // Set look and feel
        // -----------------
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Throwable e) {
            // Do nothing.
            // If we can't set the desired look and feel, UIManager does
            // automaticaly the right thing for us.
        }

        // Display a progress indicator while we are loading the drawing
        // ----------------------------------------------------------
        Container c = getContentPane();
        final ProgressIndicator progress = new ProgressIndicator(
                getName(), labels.getString("progressInitializing"));
        c.add(progress);
        progress.revalidate();

        // Load the drawing using a worker thread
        // --------------------------------------
        new Worker() {

            public Object construct() {
                try {
                    Thread t = new Thread() {

                        public void run() {
                            drawingComponent = createDrawingComponent();
                        }
                    };
                    t.start();
                    progress.setNote(labels.getString("progressLoading"));
                    long start = System.currentTimeMillis();
                    Object drawing = loadDrawing(progress);
                    long end = System.currentTimeMillis();
                    System.out.println("AnyWikiDraw loading time:" + (end - start));
                    progress.setNote(labels.getString("progressOpeningEditor"));
                    progress.setIndeterminate(true);
                    t.join();
                    return drawing;
                } catch (Throwable t) {
                    return t;
                }
            }

            public void finished(Object result) {
                JComponent c = (JComponent) getContentPane();
//                c.setBorder(new LineBorder(new Color(0xa5a5a5)));
                c.setBorder(new LineBorder(new Color(0x202020)));
                c.setLayout(new BorderLayout());
                c.removeAll();
                if (result instanceof Throwable) {
                    Throwable error = (Throwable) result;
                    error.printStackTrace();
                    String message = (error.getMessage() == null) ? error.toString() : error.getMessage();
                    MessagePanel mp = new MessagePanel(
                            UIManager.getIcon("OptionPane.errorIcon"),
                            labels.getFormatted("messageLoadFailed", htmlencode(getParameter("DrawingURL")), htmlencode(message)));
                    c.add(mp);
                    mp.addActionListener(new ActionListener() {

                        public void actionPerformed(ActionEvent evt) {
                            if (evt.getActionCommand().equals("close")) {
                                close();
                            }
                        }
                    });
                } else {
                    c.add(drawingComponent.getComponent());
                    drawingComponent.addActionListener(new ActionListener() {

                        public void actionPerformed(ActionEvent evt) {
                            if (evt.getActionCommand().equals("save")) {
                                save();
                            } else if (evt.getActionCommand().equals("cancel")) {
                                cancel();
                            }
                        }
                    });

                    initComponents();
                    if (result != null) {
                        if (result instanceof Drawing) {
                            setDrawing((Drawing) result);
                        } else if (result instanceof Throwable) {
                            setDrawing(createDrawing());
                            getDrawing().add(new SVGTextFigure(result.toString()));
                            ((Throwable) result).printStackTrace();
                        }
                    }
                }
                c.validate();
                long end = System.currentTimeMillis();
                System.out.println("AbstractDrawingApplet startup latency:" + (end - start));
            }
        }.start();
    }

    /**
     * Sets the drawing on the drawing panel.
     */
    private void setDrawing(Drawing d) {
        drawingComponent.setDrawing(d);
    }

    /**
     * Gets the drawing from the drawing panel.
     */
    private Drawing getDrawing() {
        return drawingComponent.getDrawing();
    }

    /**
     * Gets the version of the applet.
     */
    public String getVersion() {
        if (version == null) {
            BufferedReader r = null;
            try {
                InputStream resource = AbstractDrawingApplet.class.getResourceAsStream("version.txt");
                r = new BufferedReader(new InputStreamReader(resource, "UTF-8"));
                version = r.readLine();
            } catch (IOException e) {
                version = "unknown";
            } catch (NullPointerException e) {
                version = "unknown";
            } finally {
                if (r != null) {
                    try {
                        r.close();
                    } catch (IOException e) {
                        // suppress
                    }
                }
            }
        }
        return version;
    }

    /**
     * Returns information about the applet.
     */
    public String getAppletInfo() {
        return getName() +
                "\nVersion " + getVersion() +
                "\n\nCopyright (c) by the authors of AnyWikiDraw.org" +
                "\nThis software is licensed under LGPL or" +
                "\nCreative Commons 2.5 BY";
    }

    /**
     * Creates the drawing.
     */
    abstract protected Drawing createDrawing();

    /**
     * Creates the drawing component.
     */
    abstract protected DrawingComponent createDrawingComponent();

    /**
     * Returns the drawing component.
     */
    protected DrawingComponent getDrawingComponent() {
        return drawingComponent;
    }

    /**
     * Displays a progress indicator and then invokes <code>saveDrawing</code>
     * on a worker thread. Closes the applet when finished successfully.
     * Displays an error message when finished unsuccessfully.
     *
     * @see #loadDrawing
     */
    final public void save() {
        final ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.samples.svg.Labels");

        Container c = getContentPane();
        c.removeAll();
        final ProgressIndicator progress = new ProgressIndicator(
                getName(), labels.getString("progressSaving"));
        c.add(progress);
        c.validate();

        // We save the data using a worker thread
        // --------------------------------------
        new Worker() {

            public Object construct() {
                try {
                    saveDrawing(drawingComponent.getDrawing(), progress);
                    return null;
                } catch (Throwable t) {
                    return t;
                }
            }

            public void finished(Object result) {
                if (result instanceof ServerAuthenticationException) {
                    if (showAuthenticationDialog() == JOptionPane.OK_OPTION) {
                        save();
                    } else {
                        Container c = getContentPane();
                        c.removeAll();
                        c.add(drawingComponent.getComponent());
                        c.validate();
                        c.repaint();
                    }
                } else if (result instanceof Throwable) {
                    Throwable error = ((Throwable) result);
                    error.printStackTrace();
                    Container c = getContentPane();
                    c.setLayout(new BorderLayout());
                    c.removeAll();
                    String message = error.getMessage() == null ? error.toString() : error.getMessage();
                    MessagePanel mp = new MessagePanel(
                            UIManager.getIcon("OptionPane.errorIcon"),
                            labels.getFormatted("messageSaveFailed", htmlencode(getParameter("UploadURL")), htmlencode(message)));
                    c.add(mp);
                    mp.addActionListener(new ActionListener() {

                        public void actionPerformed(ActionEvent evt) {
                            if (evt.getActionCommand().equals("close")) {
                                close();
                            }
                        }
                    });
                    c.validate();
                } else {
                    close();
                }
            }
        }.start();
    }

    /**
     * Cancels the applet. Displays a dialog when the drawing contains
     * unsaved changes.
     */
    protected void cancel() {
        // XXX - Display a dialog when the drawing contains unsaved changes.
        close();
    }

    public String[][] getParameterInfo() {
        return new String[][]{
                    {"DrawingURL", "URL", "The URL of the drawing."},
                    {"DrawingName", "String", "The name of the drawing."},
                    {"DrawingRevision", "String", "The revision of the drawing to detect concurrent updates."},
                    {"DrawingWidth", "int", "The width of the drawing."},
                    {"DrawingHeight", "int", "The height of the drawing."},
                    {"PageURL", "URL", "The page to be opened when the applet is closed."},
                    {"PageName", "String", "The name of the page to be opened when the applet is closed."},
                    {"UploadURL", "URL", "The page to which the applet posts the image."},
                    {"UploadAction", "String", "The value of the action parameter in the post data."},
                    {"Locale", "String", "The locale of the user interface, for example 'en_us'."}
                };
    }

    /**
     * Loads the drawing.
     * By convention this method is invoked on a worker thread.
     *
     * @param progress A ProgressIndicator to inform the user about the progress
     * of the operation.
     * @return The Drawing that was loaded.
     */
    protected Drawing loadDrawing(ProgressIndicator progress) throws IOException {
        final ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.samples.svg.Labels");
        Drawing drawing = createDrawing();
        InputStream in = null;
        try {
            if (getParameter("DrawingURL") != null) {
                ByteArrayOutputStream buf = new ByteArrayOutputStream();
                URL url = new URL(getDocumentBase(), getParameter("DrawingURL"));
                URLConnection uc = url.openConnection();

                // Disable caching. This ensures that we always request the 
                // newest version of the drawing from the server.
                // (Note: The server still needs to set the proper HTTP caching
                // properties to prevent proxies from caching the drawing).
                if (uc instanceof HttpURLConnection) {
                    ((HttpURLConnection) uc).setUseCaches(false);
                }

                // Read the data into a buffer
                int contentLength = uc.getContentLength();
                in = uc.getInputStream();
                if (contentLength != -1) {
                    in = new BoundedRangeInputStream(in);
                    ((BoundedRangeInputStream) in).setMaximum(contentLength + 1);
                //progress.setProgressModel((BoundedRangeModel) in);
                //progress.setIndeterminate(false);
                }
                BufferedInputStream bin = new BufferedInputStream(in);
                bin.mark(512);

                // Read the data using all supported input formats
                // until we succeed
                IOException formatException = null;
                for (InputFormat format : drawing.getInputFormats()) {
                    if (format.getFileFilter().accept(new File(getParameter("DrawingURL")))) {
                        try {
                            bin.reset();
                        } catch (IOException e) {
                            uc = url.openConnection();
                            in = uc.getInputStream();
                            in = new BoundedRangeInputStream(in);
                            ((BoundedRangeInputStream) in).setMaximum(contentLength + 1);
                            //progress.setProgressModel((BoundedRangeModel) in);
                            bin = new BufferedInputStream(in);
                            bin.mark(512);
                        }
                        long start = System.currentTimeMillis();
                        try {
                            format.read(bin, drawing, true);
                            formatException = null;
                            long end = System.currentTimeMillis();
                            System.out.println("Format " + format.toString() + " elapsed:" + (end - start));
                            break;
                        } catch (IOException e) {
                            formatException = e;
                        }
                        long end = System.currentTimeMillis();
                        System.out.println("Format " + format.toString() + " elapsed:" + (end - start));
                    }
                }
                if (formatException != null) {
                    throw formatException;
                }
            }
        } finally {
            if (in != null) {
                in.close();
            }
        }
        return drawing;
    }

    /**
     * Saves the drawing.
     * By convention this method is invoked on a worker thread.
     *
     * @param drawing The Drawing to be saved.
     * @param progress A ProgressIndicator to inform the user about the progress
     * of the operation.
     * @throw IOException when an communication error occured
     * @throw ServerAuthenticationException when we couldn't save, because
     * we failed to authenticate. On this exception, the applet should open
     * an authentication dialog, and give the user a second chance to save
     * the drawing.
     */
    protected void saveDrawing(Drawing drawing,
            ProgressIndicator progress) throws IOException, ServerAuthenticationException {

        // Determine rendered size
        Double canvasWidth = AttributeKeys.CANVAS_WIDTH.get(drawing);
        Double canvasHeight = AttributeKeys.CANVAS_HEIGHT.get(drawing);
        Dimension renderedSize = (canvasWidth == null || canvasHeight == null) ?//
                new Dimension(-1, -1) : //
                new Dimension(canvasWidth.intValue(), canvasHeight.intValue());

        if (renderedSize.width == -1 || renderedSize.height == -1) {
            Rectangle2D.Double drawBounds = null;
            for (Figure f : drawing.getChildren()) {
                if (drawBounds == null) {
                    drawBounds = f.getDrawingArea();
                } else {
                    drawBounds.add(f.getDrawingArea());
                }
            }
            if (drawBounds == null) {
                drawBounds = new Rectangle2D.Double(0, 0, 100, 100);
            }
            if (renderedSize.width == -1) {
                renderedSize.width = (int) (Math.abs(drawBounds.x) + drawBounds.getWidth());
            }
            if (renderedSize.height == -1) {
                renderedSize.height = (int) (Math.abs(drawBounds.y) + drawBounds.getHeight());
            }
        }

        // Determine drawing size
        Dimension drawingSize = new Dimension(-1, -1);
        try {
            drawingSize.width = Math.max(1, Integer.parseInt(getParameter("DrawingWidth")));
        } catch (Exception e) {
        }
        try {
            drawingSize.height = Math.max(1, Integer.parseInt(getParameter("DrawingHeight")));
        } catch (Exception e) {
        }
        if (drawingSize.width == -1 || drawingSize.height == -1) {
            drawingSize.width = renderedSize.width;
            drawingSize.height = renderedSize.height;
        }

        // Write the drawing
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        String imageExtension = getParameter("DrawingName", "unnamed.svg").toLowerCase();
        imageExtension = (imageExtension == null) ? "" : imageExtension.substring(imageExtension.lastIndexOf('.') + 1);
        if (imageExtension.equals("")) {
            imageExtension = "svg";
        }
        byte[] drawingData = null;
        for (OutputFormat format : drawing.getOutputFormats()) {
            if (imageExtension.equals(format.getFileExtension())) {
                if (format instanceof ImageOutputFormat) {
                    ((ImageOutputFormat) format).write(out, drawing, new AffineTransform(), renderedSize);
                } else {
                    format.write(out, drawing);
                }
                drawingData = out.toByteArray();
                break;
            }
        }
        if (drawingData == null) {
            throw new IOException("Unsupported file format.");
        }

        // If the drawing is an SVG image, we provide a rendered PNG image of the drawing
        byte[] renderedData = null;
        byte[] imageMapData = null;
        if (imageExtension.startsWith("svg")) {
            out = new ByteArrayOutputStream();
            ImageOutputFormat imgOut = new ImageOutputFormat();
            imgOut.write(out, drawing, new AffineTransform(), renderedSize);
            renderedData = out.toByteArray();

            out = new ByteArrayOutputStream();
            ImageMapOutputFormat imgMapOut = new ImageMapOutputFormat();
            imgMapOut.write(out, drawing, new AffineTransform(), renderedSize);
            imageMapData = out.toByteArray();
        }

        // Create a HTML Form
        HtmlForm form = new HtmlForm();
        form.putString("Action", getParameter("UploadAction", ""));
        form.putString("UploadSummary", getDrawingComponent().getSummary());
        form.putString("DrawingName", getParameter("DrawingName"));
        form.putString("DrawingRevision", getParameter("DrawingRevision", ""));
        form.putString("DrawingWidth", Integer.toString(renderedSize.width));
        form.putString("DrawingHeight", Integer.toString(renderedSize.height));
        form.putFile("DrawingData", getParameter("DrawingName"), "image/" + imageExtension,
                drawingData);
        if (renderedData != null) {
            form.putFile("RenderedImageData", getParameter("DrawingName") + ".png", "image/png",
                    renderedData);
            form.putString("RenderedImageWidth", Integer.toString(renderedSize.width));
            form.putString("RenderedImageHeight", Integer.toString(renderedSize.height));
        }
        if (imageMapData != null) {
            form.putFile("ImageMapData", getParameter("DrawingName") + ".map", "text/html",
                    imageMapData);
        }


        // Post the data
        URL url = new URL(getDocumentBase(), getParameter("UploadURL"));
        HttpRequest request = new HttpRequest();
        request.open("POST", url);
        request.send(form);
        if (request.getResponseCode() != 200) {
            throw new IOException(request.getResponseCode() + " " + request.getResponseMessage() + "\n" + request.getResponseDataAsString());
        }
    }

    /**
     * Shows an authentication dialog.
     *
     * This is a stub method which always returns JOptionPane.CANCEL_OPTION.
     *
     * @return JOptionPane.OK_OPTION on success, JOptionPane.CANCEL_OPTION,
     * if the user canceled the dialog.
     */
    protected int showAuthenticationDialog() {
        return JOptionPane.CANCEL_OPTION;
    }

    /**
     * Closes the applet. This method can be implemented by invoking
     * <code>getAppletContext().showDocument(...)</code>.
     */
    protected void close() {
        AppletContext appletContext;
        try {
            appletContext = getAppletContext();
        } catch (Throwable e) {
            appletContext = null;
        }
        if (appletContext == null) {
            System.exit(0);
        } else {
            try {
                appletContext.showDocument(new URL(getDocumentBase(), getParameter("PageURL")));
            } catch (MalformedURLException ex) {
                ex.printStackTrace();
            }
        }
    }

    /**
     * Escapes all '<', '>' and '&' characters in a string.
     * @param str A String.
     * @return HTMlEncoded String.
     */
    private static String htmlencode(String str) {
        if (str == null) {
            return "";
        } else {
            StringBuilder buf = new StringBuilder();
            for (char ch : str.toCharArray()) {
                switch (ch) {
                    case '<':
                        buf.append("&lt;");
                        break;
                    case '>':
                        buf.append("&gt;");
                        break;
                    case '&':
                        buf.append("&amp;");
                        break;
                    default:
                        buf.append(ch);
                        break;
                }
            }
            return buf.toString();
        }
    }

    /** This method is called from within the init() method to
     * initialize the form.
     * WARNING: Do NOT modify this code. The content of this method is
     * always regenerated by the Form Editor.
     */
    // <editor-fold defaultstate="collapsed" desc="Generated Code">//GEN-BEGIN:initComponents
    private void initComponents() {
    }// </editor-fold>//GEN-END:initComponents
    // Variables declaration - do not modify//GEN-BEGIN:variables
    // End of variables declaration//GEN-END:variables
}
