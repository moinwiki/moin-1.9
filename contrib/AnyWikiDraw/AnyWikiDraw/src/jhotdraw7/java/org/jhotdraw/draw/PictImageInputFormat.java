/**
 * @(#)PictImageInputFormat.java
 *
 * Copyright (c) 2008 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.jhotdraw.draw;

import java.awt.*;
import java.awt.datatransfer.*;
import java.awt.geom.*;
import java.awt.image.*;
import java.io.*;
import java.lang.reflect.*;
import javax.swing.*;
import org.jhotdraw.io.*;
import org.jhotdraw.util.Images;

/**
 * An input format for importing drawings using the image/x-pict format from the
 * Mac OS X clipboard.
 * <p>
 * This class uses the prototype design pattern. A ImageHolderFigure figure is used
 * as a prototype for creating a figure that holds the imported image.
 * <p>
 * XXX - This class uses the deprecated Cocoa-Java bridge.
 *
 * @author Werner Randelshofer
 * @version $Id: PictImageInputFormat.java 536 2009-06-14 12:10:57Z rawcoder $
 */
public class PictImageInputFormat implements InputFormat {

    /**
     * The prototype for creating a figure that holds the imported image.
     */
    private ImageHolderFigure prototype;
    /**
     * Format description used for the file filter.
     */
    private String description;
    /**
     * File name extension used for the file filter.
     */
    private String fileExtension;
    /**
     * Image IO image format name.
     */
    private String formatName;
    /**
     * The image type must match the output format, for example, PNG supports
     * BufferedImage.TYPE_INT_ARGB whereas GIF needs BufferedImage.TYPE_
     */
    private int imageType;
    /**
     * The image/x-pict data flavor is used by the Mac OS X clipboard. 
     */
    public final static DataFlavor PICT_FLAVOR;
    

    static {
        try {
            PICT_FLAVOR = new DataFlavor("image/x-pict");
        } catch (ClassNotFoundException e) {
            throw new InternalError("Unable to create data flavor image/x-pict");
        }
    }

    /** Creates a new image output format for Portable Network Graphics PNG. */
    public PictImageInputFormat(ImageHolderFigure prototype) {
        this(prototype, "PICT", "PICT (pct)", "pct", BufferedImage.TYPE_INT_ARGB);
    }

    /** Creates a new image output format for the specified image format.
     *
     * @param formatName The format name for the javax.imageio.ImageIO object.
     * @param description The format description to be used for the file filter.
     * @param fileExtension The file extension to be used for file filter.
     * @param bufferedImageType The BufferedImage type used to produce the image.
     *          The value of this parameter must match with the format name.
     */
    private PictImageInputFormat(ImageHolderFigure prototype, String formatName, String description, String fileExtension,
            int bufferedImageType) {
        this.prototype = prototype;
        this.formatName = formatName;
        this.description = description;
        this.fileExtension = fileExtension;
        this.imageType = bufferedImageType;
    }

    public javax.swing.filechooser.FileFilter getFileFilter() {
        return new ExtensionFileFilter(description, fileExtension);
    }

    public String getFileExtension() {
        return fileExtension;
    }

    public JComponent getInputFormatAccessory() {
        return null;
    }

    public void read(File file, Drawing drawing) throws IOException {
        read(file, drawing, true);
    }
    
    public void read(File file, Drawing drawing, boolean replace) throws IOException {
        InputStream in = null;
        try {
            in = new BufferedInputStream(new FileInputStream(file));
            Image img = getImageFromPictStream(in);
            if (img == null) {
                throw new IOException("Couldn't read pict image");
            }
            ImageHolderFigure figure = (ImageHolderFigure) prototype.clone();
            figure.setBufferedImage(Images.toBufferedImage(img));
            figure.setBounds(
                    new Point2D.Double(0, 0),
                    new Point2D.Double(
                    figure.getBufferedImage().getWidth(),
                    figure.getBufferedImage().getHeight()));
            if (replace) {
                drawing.removeAllChildren();
            }
            drawing.basicAdd(figure);
        } finally {
            in.close();
        }
    }

    public void read(InputStream in, Drawing drawing, boolean replace) throws IOException {
        try {
            Image img = getImageFromPictStream(in);
            if (img == null) {
                throw new IOException("Couldn't read pict image");
            }
            ImageHolderFigure figure = (ImageHolderFigure) prototype.clone();
            figure.setBufferedImage(Images.toBufferedImage(img));
            figure.setBounds(
                    new Point2D.Double(0, 0),
                    new Point2D.Double(
                    figure.getBufferedImage().getWidth(),
                    figure.getBufferedImage().getHeight()));
            if (replace) {
                drawing.removeAllChildren();
            }
            drawing.basicAdd(figure);
        } finally {
            in.close();
        }
    }

    public ImageHolderFigure createImageHolder(InputStream in) throws IOException {
        ImageHolderFigure figure = (ImageHolderFigure) prototype.clone();
        figure.setBufferedImage(Images.toBufferedImage(getImageFromPictStream(in)));
        figure.setBounds(
                new Point2D.Double(0, 0),
                new Point2D.Double(
                figure.getBufferedImage().getWidth(),
                figure.getBufferedImage().getHeight()));
        return figure;
    }

    public boolean isDataFlavorSupported(DataFlavor flavor) {
        return flavor.equals(PICT_FLAVOR);
    }

    public void read(Transferable t, Drawing drawing, boolean replace) throws UnsupportedFlavorException, IOException {
        Object data = t.getTransferData(PICT_FLAVOR);
        if (data instanceof InputStream) {
            InputStream in = null;
            try {
                in = (InputStream) data;
                Image img = getImageFromPictStream(in);
                if (img == null) {
                    throw new IOException("Couldn't read pict image");
                }
                ImageHolderFigure figure = (ImageHolderFigure) prototype.clone();
                figure.setBufferedImage(Images.toBufferedImage(img));
                figure.setBounds(
                        new Point2D.Double(0, 0),
                        new Point2D.Double(
                        figure.getBufferedImage().getWidth(),
                        figure.getBufferedImage().getHeight()));
                if (replace) {
                    drawing.removeAllChildren();
                }
                drawing.add(figure);
            } finally {
                in.close();
            }
        }
    }
    /*
     * Converts a PICT to an AWT image using QuickTime for Java.
     * This code was contributed by Gord Peters.
     * 
     * XXX - This code performs extremly slow. We should replace it by JNI
     * code which directly accesses the native clipboard.
     */
    @SuppressWarnings("unchecked")
    private static Image getImageFromPictStream(InputStream is) throws IOException {
        try {
            ByteArrayOutputStream baos = new ByteArrayOutputStream();
            // We need to strip the header from the data because a PICT file
            // has a 512 byte header and then the data, but in our case we only
            // need the data. --GP
            byte[] header = new byte[512];
            byte[] buf = new byte[4096];
            int retval = 0, size = 0;
            baos.write(header, 0, 512);
            while ((retval = is.read(buf, 0, 4096)) > 0) {
                baos.write(buf, 0, retval);
            }
            baos.close();
            size = baos.size();
            //IJ.log("size: "+size); IJ.wait(2000);
            if (size <= 0) {
                return null;
            }
            byte[] imgBytes = baos.toByteArray();
            // Again with the uglyness.  Here we need to use the Quicktime
            // for Java code in order to create an Image object from
            // the PICT data we received on the clipboard.  However, in
            // order to get this to compile on other platforms, we use
            // the Java reflection API.
            //
            // For reference, here is the equivalent code without
            // reflection:
            //
            //
            // if (QTSession.isInitialized() == false) {
            //     QTSession.open();
            // }
            // QTHandle handle= new QTHandle(imgBytes);
            // GraphicsImporter gi=
            //     new GraphicsImporter(QTUtils.toOSType("PICT"));
            // gi.setDataHandle(handle);
            // QDRect qdRect= gi.getNaturalBounds();
            // GraphicsImporterDrawer gid= new GraphicsImporterDrawer(gi);
            // QTImageProducer qip= new QTImageProducer(gid,
            //                          new Dimension(qdRect.getWidth(),
            //                                        qdRect.getHeight()));
            // return(Toolkit.getDefaultToolkit().createImage(qip));
            //
            // --GP
            //IJ.log("quicktime.QTSession");
            Class c = Class.forName("quicktime.QTSession");
            Method m = c.getMethod("isInitialized");
            Boolean b = (Boolean) m.invoke(null, (Object[]) null);
            if (b.booleanValue() == false) {
                m = c.getMethod("open");
                m.invoke(null);
            }
            c = Class.forName("quicktime.util.QTHandle");
            Constructor con = c.getConstructor(new Class[]{imgBytes.getClass()});
            Object handle = con.newInstance(new Object[]{imgBytes});
            String s = new String("PICT");
            c = Class.forName("quicktime.util.QTUtils");
            m = c.getMethod("toOSType", new Class[]{s.getClass()});
            Integer type = (Integer) m.invoke(null, new Object[]{s});
            c = Class.forName("quicktime.std.image.GraphicsImporter");
            con = c.getConstructor(new Class[]{type.TYPE});
            Object importer = con.newInstance(new Object[]{type});
            m = c.getMethod("setDataHandle",
                    new Class[]{Class.forName("quicktime.util." + "QTHandleRef")});
            m.invoke(importer, new Object[]{handle});
            m = c.getMethod("getNaturalBounds");
            Object rect = m.invoke(importer);
            c = Class.forName("quicktime.app.view.GraphicsImporterDrawer");
            con = c.getConstructor(new Class[]{importer.getClass()});
            Object iDrawer = con.newInstance(new Object[]{importer});
            m = rect.getClass().getMethod("getWidth");
            Integer width = (Integer) m.invoke(rect);
            m = rect.getClass().getMethod("getHeight");
            Integer height = (Integer) m.invoke(rect);
            Dimension d = new Dimension(width.intValue(), height.intValue());
            c = Class.forName("quicktime.app.view.QTImageProducer");
            con = c.getConstructor(new Class[]{iDrawer.getClass(), d.getClass()});
            Object producer = con.newInstance(new Object[]{iDrawer, d});
            if (producer instanceof ImageProducer) {
                return (Toolkit.getDefaultToolkit().createImage((ImageProducer) producer));
            }
        } catch (Exception e) {
            IOException error = new IOException("Couldn't read PICT image");
            error.initCause(e);
            throw error;
        }
        IOException error = new IOException("Couldn't read PICT image");
        throw error;
    }
}
