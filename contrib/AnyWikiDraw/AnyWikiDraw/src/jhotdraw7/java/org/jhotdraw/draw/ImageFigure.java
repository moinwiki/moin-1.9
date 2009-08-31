/*
 * @(#)ImageFigure.java
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
package org.jhotdraw.draw;

import java.awt.*;
import java.awt.geom.*;
import java.awt.image.*;
import java.io.*;
import java.util.*;
import javax.imageio.*;
import javax.swing.*;
import org.jhotdraw.geom.*;
import org.jhotdraw.io.Base64;
import org.jhotdraw.util.*;
import org.jhotdraw.xml.*;
import static org.jhotdraw.draw.AttributeKeys.*;

/**
 * An {@link ImageHolderFigure} which holds a buffered image.
 * <p>
 * A DrawingEditor should provide the ImageTool to create an ImageFigure.
 *
 * @see ImageTool
 *
 * @author Werner Randelshofer
 * @version $Id: ImageFigure.java 531 2009-06-13 10:20:39Z rawcoder $
 */
public class ImageFigure extends AbstractAttributedDecoratedFigure
        implements ImageHolderFigure {

    /**
     * This rectangle describes the bounds into which we draw the image.
     */
    private Rectangle2D.Double rectangle;
    /**
     * The image data. This can be null, if the image was created from a
     * BufferedImage.
     */
    private byte[] imageData;
    /**
     * The buffered image. This can be null, if we haven't yet parsed the
     * imageData.
     */
    private transient BufferedImage bufferedImage;

    /** Creates a new instance. */
    public ImageFigure() {
        this(0, 0, 0, 0);
    }

    public ImageFigure(double x, double y, double width, double height) {
        rectangle = new Rectangle2D.Double(x, y, width, height);
    }

    // DRAWING
    protected void drawFigure(Graphics2D g) {
        if (AttributeKeys.FILL_COLOR.get(this) != null) {
            g.setColor(AttributeKeys.FILL_COLOR.get(this));
            drawFill(g);
        }
        drawImage(g);

        if (STROKE_COLOR.get(this) != null && STROKE_WIDTH.get(this) > 0d) {
            g.setStroke(AttributeKeys.getStroke(this));
            g.setColor(STROKE_COLOR.get(this));

            drawStroke(g);
        }
        if (TEXT_COLOR.get(this) != null) {
            if (TEXT_SHADOW_COLOR.get(this) != null &&
                    TEXT_SHADOW_OFFSET.get(this) != null) {
                Dimension2DDouble d = TEXT_SHADOW_OFFSET.get(this);
                g.translate(d.width, d.height);
                g.setColor(TEXT_SHADOW_COLOR.get(this));
                drawText(g);
                g.translate(-d.width, -d.height);
            }
            g.setColor(TEXT_COLOR.get(this));
            drawText(g);
        }
    }

    protected void drawFill(Graphics2D g) {
        Rectangle2D.Double r = (Rectangle2D.Double) rectangle.clone();
        double grow = AttributeKeys.getPerpendicularFillGrowth(this);
        Geom.grow(r, grow, grow);
        g.fill(r);
    }

    protected void drawImage(Graphics2D g) {
        BufferedImage image = getBufferedImage();
        if (image != null) {
            g.drawImage(image, (int) rectangle.x, (int) rectangle.y, (int) rectangle.width, (int) rectangle.height, null);
        } else {
            g.setStroke(new BasicStroke());
            g.setColor(Color.red);
            g.draw(rectangle);
            g.draw(new Line2D.Double(rectangle.x, rectangle.y, rectangle.x + rectangle.width, rectangle.y + rectangle.height));
            g.draw(new Line2D.Double(rectangle.x + rectangle.width, rectangle.y, rectangle.x, rectangle.y + rectangle.height));
        }
    }

    protected void drawStroke(Graphics2D g) {
        Rectangle2D.Double r = (Rectangle2D.Double) rectangle.clone();
        double grow = AttributeKeys.getPerpendicularDrawGrowth(this);
        Geom.grow(r, grow, grow);

        g.draw(r);
    }

    // SHAPE AND BOUNDS
    public Rectangle2D.Double getBounds() {
        Rectangle2D.Double bounds = (Rectangle2D.Double) rectangle.clone();
        return bounds;
    }

    @Override
    public Rectangle2D.Double getFigureDrawingArea() {
        Rectangle2D.Double r = (Rectangle2D.Double) rectangle.clone();
        double grow = AttributeKeys.getPerpendicularHitGrowth(this);
        Geom.grow(r, grow, grow);
        return r;
    }

    /**
     * Checks if a Point2D.Double is inside the figure.
     */
    public boolean figureContains(Point2D.Double p) {
        Rectangle2D.Double r = (Rectangle2D.Double) rectangle.clone();
        double grow = AttributeKeys.getPerpendicularHitGrowth(this) + 1d;
        Geom.grow(r, grow, grow);
        return r.contains(p);
    }

    public void setBounds(Point2D.Double anchor, Point2D.Double lead) {
        rectangle.x = Math.min(anchor.x, lead.x);
        rectangle.y = Math.min(anchor.y, lead.y);
        rectangle.width = Math.max(0.1, Math.abs(lead.x - anchor.x));
        rectangle.height = Math.max(0.1, Math.abs(lead.y - anchor.y));
    }

    /**
     * Transforms the figure.
     * @param tx The transformation.
     */
    public void transform(AffineTransform tx) {
        Point2D.Double anchor = getStartPoint();
        Point2D.Double lead = getEndPoint();
        setBounds(
                (Point2D.Double) tx.transform(anchor, anchor),
                (Point2D.Double) tx.transform(lead, lead));
    }
    // ATTRIBUTES

    public void restoreTransformTo(Object geometry) {
        rectangle.setRect((Rectangle2D.Double) geometry);
    }

    public Object getTransformRestoreData() {
        return (Rectangle2D.Double) rectangle.clone();
    }

    // EDITING
    @Override
    public Collection<Action> getActions(Point2D.Double p) {
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels");
        LinkedList<Action> actions = new LinkedList<Action>();
        return actions;
    }
    // CONNECTING

    public Connector findConnector(Point2D.Double p, ConnectionFigure prototype) {
        // XXX - This doesn't work with a transformed rect
        return new ChopRectangleConnector(this);
    }

    public Connector findCompatibleConnector(Connector c, boolean isStartConnector) {
        // XXX - This doesn't work with a transformed rect
        return new ChopRectangleConnector(this);
    }

    // COMPOSITE FIGURES
    // CLONING
    public ImageFigure clone() {
        ImageFigure that = (ImageFigure) super.clone();
        that.rectangle = (Rectangle2D.Double) this.rectangle.clone();
        return that;
    }

    public void read(DOMInput in) throws IOException {
        super.read(in);
        if (in.getElementCount("imageData") > 0) {
            in.openElement("imageData");
            String base64Data = in.getText();
            if (base64Data != null) {
                setImageData(Base64.decode(base64Data));
            }
            in.closeElement();
        }
    }

    public void write(DOMOutput out) throws IOException {
        super.write(out);
        if (getImageData() != null) {
            out.openElement("imageData");
            out.addText(Base64.encodeBytes(getImageData()));
            out.closeElement();
        }
    }

    /**
     * Sets the image.
     *
     * @param imageData The image data. If this is null, a buffered image must
     * be provided.
     * @param bufferedImage An image constructed from the imageData. If this
     * is null, imageData must be provided.
     */
    public void setImage(byte[] imageData, BufferedImage bufferedImage) {
        willChange();
        this.imageData = imageData;
        this.bufferedImage = bufferedImage;
        changed();
    }

    /**
     * Sets the image data.
     * This clears the buffered image.
     */
    public void setImageData(byte[] imageData) {
        willChange();
        this.imageData = imageData;
        this.bufferedImage = null;
        changed();
    }

    /**
     * Sets the buffered image.
     * This clears the image data.
     */
    public void setBufferedImage(BufferedImage image) {
        willChange();
        this.imageData = null;
        this.bufferedImage = image;
        changed();
    }

    /**
     * Gets the buffered image. If necessary, this method creates the buffered
     * image from the image data.
     */
    public BufferedImage getBufferedImage() {
        if (bufferedImage == null && imageData != null) {
            try {
                bufferedImage = ImageIO.read(new ByteArrayInputStream(imageData));
            } catch (IOException e) {
                e.printStackTrace();
                // If we can't create a buffered image from the image data,
                // there is no use to keep the image data and try again, so
                // we drop the image data.
                imageData = null;
            }
        }
        return bufferedImage;
    }

    /**
     * Gets the image data. If necessary, this method creates the image
     * data from the buffered image.
     */
    public byte[] getImageData() {
        if (bufferedImage != null && imageData == null) {
            try {
                ByteArrayOutputStream bout = new ByteArrayOutputStream();
                ImageIO.write(bufferedImage, "PNG", bout);
                bout.close();
                imageData = bout.toByteArray();
            } catch (IOException e) {
                e.printStackTrace();
                // If we can't create image data from the buffered image,
                // there is no use to keep the buffered image and try again, so
                // we drop the buffered image.
                bufferedImage = null;
            }
        }
        return imageData;
    }

    public void loadImage(File file) throws IOException {
        InputStream in = null;
        try {
            in = new FileInputStream(file);
            loadImage(in);
        } catch (Throwable t) {
            ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels");
            IOException e = new IOException(labels.getFormatted("file.failedToLoadImage.message", file.getName()));
            e.initCause(t);
            throw e;
        } finally {
            if (in != null) {
                in.close();
            }
        }
    }

    public void loadImage(InputStream in) throws IOException {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        byte[] buf = new byte[512];
        int bytesRead;
        while ((bytesRead = in.read(buf)) > 0) {
            baos.write(buf, 0, bytesRead);
        }
        BufferedImage img = ImageIO.read(new ByteArrayInputStream(baos.toByteArray()));
        if (img == null) {
            ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels");
            throw new IOException(labels.getFormatted("file.failedToLoadImage.message", in.toString()));
        }
        imageData = baos.toByteArray();
        bufferedImage = img;
    }

    private void writeObject(ObjectOutputStream out) throws IOException {
        // The call to getImageData() ensures that we have serializable data
        // in the imageData array.
        getImageData();
        out.defaultWriteObject();
        }
}