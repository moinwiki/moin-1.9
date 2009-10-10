 /*
 * @(#)SVGImage.java
 *
 * Copyright (c) 1996-2008 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * This software is the confidential and proprietary information of
 * JHotDraw.org ("Confidential Information"). You shall not disclose
 * such Confidential Information and shall use it only in accordance
 * with the terms of the license agreement you entered into with
 * JHotDraw.org.
 */
package org.jhotdraw.samples.svg.figures;

import java.awt.*;
import java.awt.event.*;
import java.awt.geom.*;
import java.awt.image.*;
import java.io.*;
import java.util.*;
import javax.imageio.ImageIO;
import javax.swing.*;
import org.jhotdraw.draw.*;
import static org.jhotdraw.samples.svg.SVGAttributeKeys.*;
import org.jhotdraw.samples.svg.*;
import org.jhotdraw.util.*;
import org.jhotdraw.geom.*;

/**
 * SVGImage.
 *
 * @author Werner Randelshofer
 * @version $Id: SVGImageFigure.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class SVGImageFigure extends SVGAttributedFigure implements SVGFigure, ImageHolderFigure {

    /**
     * This rectangle describes the bounds into which we draw the image.
     */
    private Rectangle2D.Double rectangle;
    /**
     * This is used to perform faster drawing.
     */
    private transient Shape cachedTransformedShape;
    /**
     * This is used to perform faster hit testing.
     */
    private transient Shape cachedHitShape;
    /**
     * The image data. This can be null, if the image was created from a
     * BufferedImage.
     */
    private byte[] imageData;
    /**
     * The buffered image. This can be null, if we haven't yet parsed the
     * imageData.
     */
    private BufferedImage bufferedImage;

    /** Creates a new instance. */
    public SVGImageFigure() {
        this(0, 0, 0, 0);
    }

    public SVGImageFigure(double x, double y, double width, double height) {
        rectangle = new Rectangle2D.Double(x, y, width, height);
        SVGAttributeKeys.setDefaults(this);
    }

    // DRAWING
    @Override
    public void draw(Graphics2D g) {
        //super.draw(g);

        double opacity = OPACITY.get(this);
        opacity = Math.min(Math.max(0d, opacity), 1d);
        if (opacity != 0d) {
            Composite savedComposite = g.getComposite();
            if (opacity != 1d) {
                g.setComposite(AlphaComposite.getInstance(AlphaComposite.SRC_OVER, (float) opacity));
            }

            BufferedImage image = getBufferedImage();
            if (image != null) {
                if (TRANSFORM.get(this) != null) {
                    // FIXME - We should cache the transformed image.
                    //         Drawing a transformed image appears to be very slow.
                    Graphics2D gx = (Graphics2D) g.create();
                    
                    // Use same rendering hints like parent graphics
                    gx.setRenderingHints(g.getRenderingHints());
                    
                    gx.transform(TRANSFORM.get(this));
                    gx.drawImage(image, (int) rectangle.x, (int) rectangle.y, (int) rectangle.width, (int) rectangle.height, null);
                    gx.dispose();
                } else {
                    g.drawImage(image, (int) rectangle.x, (int) rectangle.y, (int) rectangle.width, (int) rectangle.height, null);
                }
            } else {
                Shape shape = getTransformedShape();
                g.setColor(Color.red);
                g.setStroke(new BasicStroke());
                g.draw(shape);
            }

            if (opacity != 1d) {
                g.setComposite(savedComposite);
            }
        }
    }

    protected void drawFill(Graphics2D g) {

    }

    protected void drawStroke(Graphics2D g) {

    }

    // SHAPE AND BOUNDS
    public double getX() {
        return rectangle.x;
    }

    public double getY() {
        return rectangle.y;
    }

    public double getWidth() {
        return rectangle.width;
    }

    public double getHeight() {
        return rectangle.height;
    }

    public Rectangle2D.Double getBounds() {
        return (Rectangle2D.Double) rectangle.clone();
    }

    @Override
    public Rectangle2D.Double getDrawingArea() {
        Rectangle2D rx = getTransformedShape().getBounds2D();
        Rectangle2D.Double r = (rx instanceof Rectangle2D.Double) ? (Rectangle2D.Double) rx : new Rectangle2D.Double(rx.getX(), rx.getY(), rx.getWidth(), rx.getHeight());
        return r;
    }

    /**
     * Checks if a Point2D.Double is inside the figure.
     */
    public boolean contains(Point2D.Double p) {
        return getHitShape().contains(p);
    }

    public void setBounds(Point2D.Double anchor, Point2D.Double lead) {
        invalidateTransformedShape();
        rectangle.x = Math.min(anchor.x, lead.x);
        rectangle.y = Math.min(anchor.y, lead.y);
        rectangle.width = Math.max(0.1, Math.abs(lead.x - anchor.x));
        rectangle.height = Math.max(0.1, Math.abs(lead.y - anchor.y));
    }

    private void invalidateTransformedShape() {
        cachedTransformedShape = null;
        cachedHitShape = null;
    }

    private Shape getTransformedShape() {
        if (cachedTransformedShape == null) {
            cachedTransformedShape = (Shape) rectangle.clone();
            if (TRANSFORM.get(this) != null) {
                cachedTransformedShape = TRANSFORM.get(this).createTransformedShape(cachedTransformedShape);
            }
        }
        return cachedTransformedShape;
    }

    private Shape getHitShape() {
        if (cachedHitShape == null) {
            cachedHitShape = new GrowStroke(
                    (float) SVGAttributeKeys.getStrokeTotalWidth(this) / 2f,
                    (float) SVGAttributeKeys.getStrokeTotalMiterLimit(this)).createStrokedShape(getTransformedShape());
        }
        return cachedHitShape;
    }

    /**
     * Transforms the figure.
     * @param tx The transformation.
     */
    public void transform(AffineTransform tx) {
        invalidateTransformedShape();
        if (TRANSFORM.get(this) != null ||
                (tx.getType() & (AffineTransform.TYPE_TRANSLATION | AffineTransform.TYPE_MASK_SCALE)) != tx.getType()) {
            if (TRANSFORM.get(this) == null) {
                TRANSFORM.basicSet(this, (AffineTransform) tx.clone());
            } else {
                AffineTransform t = TRANSFORM.getClone(this);
                t.preConcatenate(tx);
                TRANSFORM.basicSet(this, t);
            }
        } else {
            Point2D.Double anchor = getStartPoint();
            Point2D.Double lead = getEndPoint();
            setBounds(
                    (Point2D.Double) tx.transform(anchor, anchor),
                    (Point2D.Double) tx.transform(lead, lead));
        }
    }
    // ATTRIBUTES
    public void restoreTransformTo(Object geometry) {
        invalidateTransformedShape();
        Object[] o = (Object[]) geometry;
        rectangle = (Rectangle2D.Double) ((Rectangle2D.Double) o[0]).clone();
        if (o[1] == null) {
            TRANSFORM.basicSet(this, null);
        } else {
            TRANSFORM.basicSet(this, (AffineTransform) ((AffineTransform) o[1]).clone());
        }
    }

    public Object getTransformRestoreData() {
        return new Object[]{
            rectangle.clone(),
            TRANSFORM.get(this)
        };
    }

    // EDITING
    @Override
    public Collection<Handle> createHandles(int detailLevel) {
        LinkedList<Handle> handles = new LinkedList<Handle>();

        switch (detailLevel % 2) {
            case -1 : // Mouse hover handles
                handles.add(new BoundsOutlineHandle(this,false,true));
                break;
            case 0:
                ResizeHandleKit.addResizeHandles(this, handles);
                handles.add(new LinkHandle(this));
                break;
            case 1:
                TransformHandleKit.addTransformHandles(this, handles);
                break;
            default:
                break;
        }
        return handles;
    }

    @Override
    public Collection<Action> getActions(Point2D.Double p) {
        final ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.samples.svg.Labels");
        LinkedList<Action> actions = new LinkedList<Action>();
        if (TRANSFORM.get(this) != null) {
            actions.add(new AbstractAction(labels.getString("edit.removeTransform.text")) {

                public void actionPerformed(ActionEvent evt) {
                    willChange();
                    fireUndoableEditHappened(
                            TRANSFORM.setUndoable(SVGImageFigure.this, null)
                            );
                    changed();
                }
            });
        }
        return actions;
    }
    // CONNECTING
    @Override
    public boolean canConnect() {
        return false; // SVG does not support connecting
    }

    @Override
    public Connector findConnector(Point2D.Double p, ConnectionFigure prototype) {
        return null; // SVG does not support connectors
    }

    @Override
    public Connector findCompatibleConnector(Connector c, boolean isStartConnector) {
        return null; // SVG does not support connectors
    }

    // COMPOSITE FIGURES
    // CLONING
    @Override
    public SVGImageFigure clone() {
        SVGImageFigure that = (SVGImageFigure) super.clone();
        that.rectangle = (Rectangle2D.Double) this.rectangle.clone();
        that.cachedTransformedShape = null;
        that.cachedHitShape = null;
        return that;
    }

    public boolean isEmpty() {
        Rectangle2D.Double b = getBounds();
        return b.width <= 0 || b.height <= 0 || imageData == null && bufferedImage == null;
    }

    @Override
    public void invalidate() {
        super.invalidate();
        invalidateTransformedShape();
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
            //System.out.println("recreateing bufferedImage");
            try {
                bufferedImage = ImageIO.read(new ByteArrayInputStream(imageData));
            } catch (Throwable e) {
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
        BufferedImage img;
        try {
            img = ImageIO.read(new ByteArrayInputStream(baos.toByteArray()));
        } catch (Throwable t) {
            img = null;
        }
        if (img == null) {
            ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels");
            throw new IOException(labels.getFormatted("file.failedToLoadImage.message", in.toString()));
        }
        imageData = baos.toByteArray();
        bufferedImage = img;
    }
}
