/*
 * @(#)TWikiDrawingApplet.java
 *
 * Copyright (c) 2007-2008 by the original authors of AnyWikiDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the AnyWikiDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */

package org.anywikidraw.twiki;

import java.awt.*;
import java.awt.geom.*;
import java.awt.image.*;
import java.io.*;
import java.net.*;
import java.text.MessageFormat;
import java.util.*;
import javax.swing.*;
import org.jhotdraw.draw.*;
import org.anywikidraw.any.*;
import org.jhotdraw.samples.svg.figures.*;
import org.jhotdraw.samples.svg.gui.*;
import org.jhotdraw.samples.svg.io.*;
import static org.jhotdraw.samples.svg.SVGAttributeKeys.*;
/**
 * TWikiDrawingApplet.
 *
 * @author Werner Randelshofer
 * @version $Id: TWikiDrawingApplet.java 118 2009-06-27 11:07:27Z rawcoder $
 */
public class TWikiDrawingApplet extends AbstractDrawingApplet {
    public TWikiDrawingApplet() {
        setName(MessageFormat.format(
                "AnyWikiDraw {0} for TWiki", getVersion()
                ));
    }
    
    public static void main(String[] args) {
        SwingUtilities.invokeLater(new Runnable() {
            public void run() {
                TWikiDrawingApplet applet = new TWikiDrawingApplet();
                JFrame f = new JFrame(applet.getName());
                f.getContentPane().setLayout(new BorderLayout());
                f.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
                f.getContentPane().add(applet, BorderLayout.CENTER);
                f.setSize(400, 400);
                applet.init();
                f.setVisible(true);
            }
        });
    }
    
    /**
     * Creates the drawing.
     */
    @Override protected Drawing createDrawing() {
        DefaultDrawing drawing = new DefaultDrawing();
        LinkedList<InputFormat> inputFormats = new LinkedList<InputFormat>();
        inputFormats.add(new SVGZInputFormat());
        inputFormats.add(new ImageInputFormat(new SVGImageFigure()));
        inputFormats.add(new ImageInputFormat(new SVGImageFigure(),"JPEG","JPEG","jpg",BufferedImage.TYPE_INT_RGB));
        LinkedList<OutputFormat> outputFormats = new LinkedList<OutputFormat>();
        outputFormats.add(new SVGOutputFormat());
        outputFormats.add(new SVGZOutputFormat());
        outputFormats.add(new ImageOutputFormat());
        outputFormats.add(new ImageOutputFormat("JPG","Joint Photographics Experts Group (JPEG)", "jpg", BufferedImage.TYPE_INT_RGB));
        outputFormats.add(new ImageOutputFormat("BMP","Windows Bitmap (BMP)", "bmp", BufferedImage.TYPE_BYTE_INDEXED));
        drawing.setInputFormats(inputFormats);
        drawing.setOutputFormats(outputFormats);
        
        if (getParameter("DrawingWidth") != null &&
                getParameter("DrawingHeight") != null) {
            try {
                double imageWidth = Double.parseDouble(getParameter("DrawingWidth"));
                double imageHeight = Double.parseDouble(getParameter("DrawingHeight"));
                if (imageWidth > 0 && imageHeight > 0) {
                    CANVAS_WIDTH.set(drawing, imageWidth);
                    CANVAS_HEIGHT.set(drawing, imageHeight);
                }
            } catch (NumberFormatException e) {

            }
        }
        
        return drawing;
    }
    @Override protected DrawingComponent createDrawingComponent() {
        return new DrawingPanel();
    }
    @Override protected DrawingPanel getDrawingComponent() {
        return (DrawingPanel) super.getDrawingComponent();
    }
    @Override protected void saveDrawing(Drawing drawing,
    ProgressIndicator progress) throws IOException, ServerAuthenticationException {
        progress.setMaximum(4);
        progress.setProgress(0);
        progress.setIndeterminate(false);
        
        
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        
        // Write the drawing
        String imageExtension = getParameter("DrawingName");
        imageExtension = (imageExtension == null) ? "" : imageExtension.substring(imageExtension.lastIndexOf('.') + 1);
        if (imageExtension.equals("")) {
            imageExtension = "svg";
        }
        byte[] drawingData = null;
        for (OutputFormat format : drawing.getOutputFormats()) {
            if (imageExtension.equals(format.getFileExtension())) {
                format.write(out, drawing);
                drawingData = out.toByteArray();
                break;
            }
        }
        if (drawingData ==  null) {
            throw new IOException("Unsupported file format.");
        }
        
        // Write a rendered version of the drawing for SVG images
        Dimension renderedSize = new Dimension(-1, -1);
        try {
            renderedSize.width = Integer.parseInt(getParameter("DrawingWidth"));
        } catch (Exception e) {
        }
        try {
            renderedSize.height = Integer.parseInt(getParameter("DrawingHeight"));
        } catch (Exception e) {
        }
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
                    drawBounds = new Rectangle2D.Double(0,0,400,300);
                    };
            if (renderedSize.width == -1) {
                renderedSize.width = (int) (Math.abs(drawBounds.x) + drawBounds.getWidth());
            }
            if (renderedSize.height == -1) {
                renderedSize.height = (int) (Math.abs(drawBounds.y) + drawBounds.getHeight());
            }
        }
        byte[] renderedData = null;
        byte[] imageMapData = null;
        if (imageExtension.startsWith("svg")) {
            out = new ByteArrayOutputStream();
            ImageOutputFormat imgOut = new ImageOutputFormat();
            imgOut.write(out, drawing, new AffineTransform(), renderedSize);
            renderedData = out.toByteArray();
            
            out = new ByteArrayOutputStream();
            OutputStreamWriter w = new OutputStreamWriter(out, "UTF-8");
            w.write("<map name=\""+getParameter("DrawingName")+"\" id=\""+getParameter("DrawingName")+"\">");
            w.flush();
            ImageMapOutputFormat imgMapOut = new ImageMapOutputFormat();
            imgMapOut.write(out, drawing, new AffineTransform(), renderedSize);
            w.write("</map>");
            w.flush();
            imageMapData = out.toByteArray();
        }
        progress.setProgress(1);
        
        // Post the drawing data
        HttpURLConnection conn = null;
        BufferedReader response = null;
        try {
            URL url = new URL(getDocumentBase(), getParameter("UploadURL"));
            conn = (HttpURLConnection) url.openConnection();
            ClientHttpRequest request = new ClientHttpRequest(conn);
            request.setParameter("filecomment", getDrawingComponent().getSummary());
            request.setParameter("filename",getParameter("DrawingName"));
            request.setParameter("noredirect","1");
            request.setParameter("filepath",getParameter("DrawingName"),
                    new ByteArrayInputStream(drawingData)
                    );
            request.post();
            
            // Read the response
            int responseCode = conn.getResponseCode();
            response = new BufferedReader(
                    new InputStreamReader(conn.getInputStream(), "UTF-8")
                    );
            StringBuilder responseText = new StringBuilder();
            for (String line; null != (line = response.readLine());) {
                responseText.append(line);
            }
            response.close();
            response = null;
            conn = null;
                if (responseText.length() > 0) {
                    IOException e2 = new IOException(responseText.toString());
                    throw e2;
                }
        } catch (IOException e) {
            if (conn != null) {
                StringBuilder responseText = new StringBuilder();
                try {
                    response = new BufferedReader(
                            new InputStreamReader(conn.getErrorStream(), "UTF-8")
                            );
                    for (String line; null != (line = response.readLine());) {
                        responseText.append(line);
                    }
                } finally {
                    if (response != null) {
                        response.close();
                        response = null;
                    }
                    
                }
                if (responseText.length() > 0) {
                    IOException e2 = new IOException(responseText.toString());
                    e2.initCause(e);
                    throw e2;
                } else {
                    throw e;
                }
            }
        } catch (Throwable e) {
                    IOException e2 = new IOException(e.getMessage());
                    e2.initCause(e);
                    throw e2;
        }
        progress.setProgress(2);
        
        // Post the rendered image
        if (renderedData != null) {
            conn = null;
            response = null;
            try {
                URL url = new URL(getDocumentBase(), getParameter("UploadURL"));
                conn = (HttpURLConnection) url.openConnection();
                ClientHttpRequest request = new ClientHttpRequest(conn);
                request.setParameter("filecomment", getDrawingComponent().getSummary());
                request.setParameter("filename",getParameter("DrawingName")+".png");
                request.setParameter("noredirect","1");
                request.setParameter("filepath",getParameter("DrawingName")+".png",
                        new ByteArrayInputStream(renderedData)
                        );
                request.post();
                
                // Read the response
                int responseCode = conn.getResponseCode();
                response = new BufferedReader(
                        new InputStreamReader(conn.getInputStream(), "UTF-8")
                        );
                StringBuilder responseText = new StringBuilder();
                for (String line; null != (line = response.readLine());) {
                    responseText.append(line);
                }
                response.close();
                response = null;
                conn = null;
                
            } catch (IOException e) {
                if (conn != null) {
                    StringBuilder responseText = new StringBuilder();
                    try {
                        response = new BufferedReader(
                                new InputStreamReader(conn.getErrorStream(), "UTF-8")
                                );
                        for (String line; null != (line = response.readLine());) {
                            responseText.append(line);
                        }
                    } finally {
                        if (response != null) {
                            response.close();
                            response = null;
                        }
                        
                    }
                    if (responseText.length() > 0) {
                        IOException e2 = new IOException(responseText.toString());
                        e2.initCause(e);
                        throw e2;
                    } else {
                        throw e;
                    }
                }
            }
        }
        progress.setProgress(3);
        
        // Post the image map
        if (imageMapData != null) {
            conn = null;
            response = null;
            try {
                URL url = new URL(getDocumentBase(), getParameter("UploadURL"));
                conn = (HttpURLConnection) url.openConnection();
                ClientHttpRequest request = new ClientHttpRequest(conn);
                request.setParameter("filecomment", getDrawingComponent().getSummary());
                request.setParameter("filename",getParameter("DrawingName")+".map");
                request.setParameter("noredirect","1");
                request.setParameter("filepath",getParameter("DrawingName")+".map",
                        new ByteArrayInputStream(imageMapData)
                        );
                request.post();
                
                // Read the response
                int responseCode = conn.getResponseCode();
                response = new BufferedReader(
                        new InputStreamReader(conn.getInputStream(), "UTF-8")
                        );
                StringBuilder responseText = new StringBuilder();
                for (String line; null != (line = response.readLine());) {
                    responseText.append(line);
                }
                response.close();
                response = null;
                conn = null;
                
            } catch (IOException e) {
                if (conn != null) {
                    StringBuilder responseText = new StringBuilder();
                    try {
                        response = new BufferedReader(
                                new InputStreamReader(conn.getErrorStream(), "UTF-8")
                                );
                        for (String line; null != (line = response.readLine());) {
                            responseText.append(line);
                        }
                    } finally {
                        if (response != null) {
                            response.close();
                            response = null;
                        }
                        
                    }
                    if (responseText.length() > 0) {
                        IOException e2 = new IOException(responseText.toString());
                        e2.initCause(e);
                        throw e2;
                    } else {
                        throw e;
                    }
                }
            }
        }
        progress.setProgress(4);
    }
    
    /** This method is called from within the init() method to
     * initialize the form.
     * WARNING: Do NOT modify this code. The content of this method is
     * always regenerated by the Form Editor.
     */
    // <editor-fold defaultstate="collapsed" desc=" Generated Code ">//GEN-BEGIN:initComponents
    private void initComponents() {

    }// </editor-fold>//GEN-END:initComponents
    
    
    // Variables declaration - do not modify//GEN-BEGIN:variables
    // End of variables declaration//GEN-END:variables
    
}
