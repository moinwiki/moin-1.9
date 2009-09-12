/*
 * @(#)DrawingPageable.java
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

package org.jhotdraw.draw;

import java.awt.*;
import java.awt.geom.*;
import java.awt.image.*;
import java.awt.print.*;
/**
 * {@code DrawingPageable} can be used to print a {@link Drawing} using the
 * java.awt.print API.
 * <p>
 * Usage:
 * <pre>
 * Pageable pageable = new DrawingPageable(aDrawing);
 * PrinterJob job = PrinterJob.getPrinterJob();
 * job.setPageable(pageable);
 * if (job.printDialog()) {
 *     try {
 *         job.print();
 *      } catch (PrinterException e) {
 *          ...inform the user that we couldn't print...
 *      }
 * }
 * </pre>
 * 
 * @author Werner Randelshofer
 * @version $Id: DrawingPageable.java 527 2009-06-07 14:28:19Z rawcoder $
 * @see org.jhotdraw.app.action.PrintAction
 */
public class DrawingPageable implements Pageable {
    private Drawing drawing;
    private PageFormat pageFormat;
    private boolean isAutorotate = false;
    
    /** Creates a new instance. */
    public DrawingPageable(Drawing drawing) {
        this.drawing = drawing;
        Paper paper = new Paper();
        pageFormat = new PageFormat();
        pageFormat.setPaper(paper);
    }
    
    public int getNumberOfPages() {
        return 1;
    }
    
    public PageFormat getPageFormat(int pageIndex) throws IndexOutOfBoundsException {
        return pageFormat;
    }
    
    public Printable getPrintable(int pageIndex) throws IndexOutOfBoundsException {
        if (pageIndex < 0 || pageIndex >= getNumberOfPages()) {
            throw new IndexOutOfBoundsException("Invalid page index:"+pageIndex);
        }
        return new Printable() {
            public int print(Graphics graphics, PageFormat pageFormat, int pageIndex) throws PrinterException {
                return printPage(graphics, pageFormat, pageIndex);
            }
        };
    }
    
    public int printPage(Graphics graphics, PageFormat pageFormat, int pageIndex) throws PrinterException {
        if (pageIndex < 0 || pageIndex >= getNumberOfPages()) {
            return Printable.NO_SUCH_PAGE;
        }
        if (drawing.getChildCount() > 0) {
            
            Graphics2D g = (Graphics2D) graphics;
            setRenderingHints(g);
            
            // Determine the draw bounds of the drawing
            Rectangle2D.Double drawBounds = null;
            for (Figure f : drawing.getChildren()) {
                if (drawBounds == null) {
                    drawBounds = f.getDrawingArea();
                } else {
                    drawBounds.add(f.getDrawingArea());
                }
            }
            
            // Setup a transformation for the drawing
            AffineTransform tx = new AffineTransform();
            tx.translate(
                    pageFormat.getImageableX(),
                    pageFormat.getImageableY()
                    );
            
            // Maybe rotate drawing
            if (isAutorotate &&
                    drawBounds.width > drawBounds.height &&
                    pageFormat.getImageableWidth() < pageFormat.getImageableHeight()) {
                
                double scaleFactor = Math.min(
                        pageFormat.getImageableWidth() / drawBounds.height,
                        pageFormat.getImageableHeight() / drawBounds.width
                        );
                tx.scale(scaleFactor, scaleFactor);
                tx.translate(drawBounds.height, 0d);
                tx.rotate(Math.PI / 2d, 0, 0);
                tx.translate(-drawBounds.x, -drawBounds.y);
            } else {
                double scaleFactor = Math.min(
                        pageFormat.getImageableWidth() / drawBounds.width,
                        pageFormat.getImageableHeight() / drawBounds.height
                        );
                tx.scale(scaleFactor, scaleFactor);
                tx.translate(-drawBounds.x, -drawBounds.y);
            }
            g.transform(tx);
            
            // Draw the drawing
            drawing.draw(g);
        }
        return Printable.PAGE_EXISTS;
    }
    protected void setRenderingHints(Graphics2D g) {
        g.setRenderingHint(RenderingHints.KEY_ALPHA_INTERPOLATION,
                RenderingHints.VALUE_ALPHA_INTERPOLATION_QUALITY);
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING,
                RenderingHints.VALUE_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_COLOR_RENDERING,
                RenderingHints.VALUE_COLOR_RENDER_QUALITY);
        g.setRenderingHint(RenderingHints.KEY_FRACTIONALMETRICS,
                RenderingHints.VALUE_FRACTIONALMETRICS_ON);
        g.setRenderingHint(RenderingHints.KEY_INTERPOLATION,
                RenderingHints.VALUE_INTERPOLATION_BICUBIC);
        g.setRenderingHint(RenderingHints.KEY_RENDERING,
                RenderingHints.VALUE_RENDER_QUALITY);
        g.setRenderingHint(RenderingHints.KEY_STROKE_CONTROL,
                RenderingHints.VALUE_STROKE_NORMALIZE);
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING,
                RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
    }
}

