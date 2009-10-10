/*
 * @(#)DnDDDrawingViewTransferHandler.java
 *
 * Copyright (c) 2009 by the original authors of JHotDraw
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
import java.awt.geom.AffineTransform;
import java.awt.geom.Point2D;
import java.awt.geom.Rectangle2D;
import java.util.*;
import javax.swing.*;

/**
 * A {@code TransferHandler} for {@code DrawingView} objects which takes
 * advantage of drag and drop features that were introduced with J2SE 6.
 * <p>
 * Note: This class requires J2SE 6. If you need backwards compatibility with
 * J2SE 5 available, you may want to use class
 * {@link DefaultDrawingViewTransferHandler} instead.
 *
 * @author Werner Randelshofer
 * @version $Id: DnDDrawingViewTransferHandler.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class DnDDrawingViewTransferHandler extends DefaultDrawingViewTransferHandler {

    private final static boolean DEBUG = false;

    /** Creates a new instance. */
    public DnDDrawingViewTransferHandler() {
    }

    @Override
    public boolean importData(TransferSupport support) {
        if (DEBUG) {
            System.out.println(this + ".importData(support)");
        }
        HashSet<Figure> transferFigures = new HashSet<Figure>();
        boolean success = support.getComponent() instanceof JComponent
                ? importData((JComponent) support.getComponent(), support.getTransferable(), transferFigures)
                : false;

        if (success) {
            final DrawingView view = (DrawingView) support.getComponent();
            Point dropPoint = support.getDropLocation().getDropPoint();
            Point2D.Double drawingDropPoint = view.viewToDrawing(dropPoint);
            //Set<Figure> transferFigures = view.getSelectedFigures();
            Rectangle2D.Double drawingArea = null;
            for (Figure fig : transferFigures) {
                if (drawingArea == null) {
                    drawingArea = fig.getDrawingArea();
                } else {
                    drawingArea.add(fig.getDrawingArea());
                }
            }
            AffineTransform t = new AffineTransform();
            t.translate(-drawingArea.x, -drawingArea.y);
            t.translate(drawingDropPoint.x, drawingDropPoint.y);
            // XXX - instead of centering, we have to translate by the drag image offset here
            t.translate(drawingArea.width / -2d, drawingArea.height / -2d);
            for (Figure fig : transferFigures) {
                fig.willChange();
                fig.transform(t);
                fig.changed();
            }
        }

        return success;
    }

}
