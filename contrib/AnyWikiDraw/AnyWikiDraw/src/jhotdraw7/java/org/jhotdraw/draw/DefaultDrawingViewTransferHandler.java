/*
 * @(#)DefaultDrawingViewTransferHandler.java
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
package org.jhotdraw.draw;

import java.awt.*;
import java.awt.datatransfer.*;
import java.awt.dnd.DragGestureEvent;
import java.awt.dnd.DragGestureListener;
import java.awt.dnd.DragGestureRecognizer;
import java.awt.dnd.DragSource;
import java.awt.dnd.DragSourceContext;
import java.awt.dnd.DragSourceDragEvent;
import java.awt.dnd.DragSourceDropEvent;
import java.awt.dnd.DragSourceEvent;
import java.awt.dnd.DragSourceListener;
import java.awt.event.*;
import java.awt.geom.Rectangle2D;
import java.awt.image.BufferedImage;
import java.io.*;
import java.util.*;
import javax.swing.*;
import javax.swing.undo.*;
import org.jhotdraw.gui.Worker;
import org.jhotdraw.gui.datatransfer.*;
import org.jhotdraw.util.ResourceBundleUtil;
import org.jhotdraw.util.ReversedList;

/**
 * Default TransferHandler for DrawingView objects.
 * <p>
 * Note: This class is here for backwards compatibilty with J2SE 5. If you
 * have J2SE 6 available, you may want to use class
 * {@link DnDDrawingViewTransferHandler} instead.
 *
 * @author Werner Randelshofer
 * @version $Id: DefaultDrawingViewTransferHandler.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class DefaultDrawingViewTransferHandler extends TransferHandler {

    private final static boolean DEBUG = false;
    /**
     * We keep the exported figures in this list, so that we don't need to
     * rely on figure selection, when method exportDone is called.
     */
    private HashSet<Figure> exportedFigures;

    /** Creates a new instance. */
    public DefaultDrawingViewTransferHandler() {
    }

    @Override
    public boolean importData(JComponent comp, Transferable t) {
        return importData(comp, t, new HashSet<Figure>());
    }

    /** Imports data and stores the transferred figures into the supplied transferFigures collection. */
    @SuppressWarnings("unchecked")
    protected boolean importData(JComponent comp, Transferable t, HashSet<Figure> transferFigures) {
        if (DEBUG) {
            System.out.println(this + ".importData(comp,t)");
        }
        boolean retValue;
        if (comp instanceof DrawingView) {
            final DrawingView view = (DrawingView) comp;
            final Drawing drawing = view.getDrawing();

            if (drawing.getInputFormats() == null ||
                    drawing.getInputFormats().size() == 0) {
                if (DEBUG) {
                    System.out.println(this + ".importData failed - drawing has no import formats");
                }
                retValue = false;
            } else {
                retValue = false;
                try {
                    // Search for a suitable input format
                    SearchLoop:
                    for (DataFlavor flavor : t.getTransferDataFlavors()) {
                        for (InputFormat format : drawing.getInputFormats()) {
                            if (DEBUG) {
                                System.out.println(this + ".importData trying to match " + format + " to flavor " + flavor);
                            }
                            if (format.isDataFlavorSupported(flavor)) {
                                if (DEBUG) {
                                    System.out.println(this + ".importData importing flavor " + flavor);
                                }
                                LinkedList<Figure> existingFigures = new LinkedList<Figure>(drawing.getChildren());
                                format.read(t, drawing, false);
                                final LinkedList<Figure> importedFigures = new LinkedList<Figure>(drawing.getChildren());
                                importedFigures.removeAll(existingFigures);
                                view.clearSelection();
                                view.addToSelection(importedFigures);
                                transferFigures.addAll(importedFigures);
                                drawing.fireUndoableEditHappened(new AbstractUndoableEdit() {

                                    @Override
                                    public String getPresentationName() {
                                        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels");
                                        return labels.getString("edit.paste.text");
                                    }

                                    @Override
                                    public void undo() throws CannotUndoException {
                                        super.undo();
                                        drawing.removeAll(importedFigures);
                                    }

                                    @Override
                                    public void redo() throws CannotRedoException {
                                        super.redo();
                                        drawing.addAll(importedFigures);
                                    }
                                });
                                retValue = true;
                                break SearchLoop;
                            }
                        }
                    }
                    // No input format found? Lets see if we got files - we
                    // can handle these
                    if (retValue == false && t.isDataFlavorSupported(DataFlavor.javaFileListFlavor)) {
                        final java.util.List<File> files = (java.util.List<File>) t.getTransferData(DataFlavor.javaFileListFlavor);
                        retValue = true;
                        final LinkedList<Figure> existingFigures = new LinkedList<Figure>(drawing.getChildren());
                        view.getEditor().setEnabled(false);
                        // FIXME - We should perform the following code in a
                        // worker thread.
                        new Worker() {

                            @Override
                            public Object construct() {
                                try {
                                    for (File file : files) {
                                        FileFormatLoop:
                                        for (InputFormat format : drawing.getInputFormats()) {
                                            if (file.isFile() &&
                                                    format.getFileFilter().accept(file)) {
                                                if (DEBUG) {
                                                    System.out.println(this + ".importData importing file " + file);
                                                }
                                                format.read(file, drawing, false);
                                            }
                                        }
                                    }
                                    return new LinkedList<Figure>(drawing.getChildren());
                                } catch (Throwable t) {
                                    return t;
                                }
                            }

                            @Override
                            public void finished(Object value) {
                                if (value instanceof Throwable) {
                                    ((Throwable) value).printStackTrace();
                                } else {
                                    final LinkedList<Figure> importedFigures = (LinkedList<Figure>) value;
                                    importedFigures.removeAll(existingFigures);
                                    if (importedFigures.size() > 0) {
                                        view.clearSelection();
                                        view.addToSelection(importedFigures);

                                        drawing.fireUndoableEditHappened(new AbstractUndoableEdit() {

                                            @Override
                                            public String getPresentationName() {
                                                ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels");
                                                return labels.getString("edit.paste.text");
                                            }

                                            @Override
                                            public void undo() throws CannotUndoException {
                                                super.undo();
                                                drawing.removeAll(importedFigures);
                                            }

                                            @Override
                                            public void redo() throws CannotRedoException {
                                                super.redo();
                                                drawing.addAll(importedFigures);
                                            }
                                        });
                                    }
                                }
                                view.getEditor().setEnabled(true);
                            }
                        }.start();
                    }
                } catch (Throwable e) {
                    if (DEBUG) {
                        e.printStackTrace();
                    }
                }
            }
        } else {
            retValue = super.importData(comp, t);
        }
        return retValue;
    }

    @Override
    public int getSourceActions(JComponent c) {
        int retValue;
        if (c instanceof DrawingView) {
            DrawingView view = (DrawingView) c;
            if (DEBUG) {
                System.out.println(this + ".getSourceActions outputFormats.size=" + view.getDrawing().getOutputFormats().size());
            }
            retValue = (view.getDrawing().getOutputFormats().size() > 0 &&
                    view.getSelectionCount() > 0) ? COPY | MOVE : NONE;
        } else {
            retValue = super.getSourceActions(c);
        }
        if (DEBUG) {
            System.out.println(this + ".getSourceActions:" + retValue);
        }
        return retValue;
    }

    @Override
    protected Transferable createTransferable(JComponent c) {
        if (DEBUG) {
            System.out.println(this + ".createTransferable(" + c + ")");
        }
        Transferable retValue;
        if (c instanceof DrawingView) {
            DrawingView view = (DrawingView) c;
            retValue = createTransferable(view, view.getSelectedFigures());
        } else {
            retValue = super.createTransferable(c);
        }

        return retValue;
    }

    protected Transferable createTransferable(DrawingView view, java.util.Set<Figure> transferFigures) {
        if (DEBUG) {
            System.out.println(this + ".createTransferable(" + view + "," + transferFigures + ")");
        }
        Transferable retValue;
        Drawing drawing = view.getDrawing();
        exportedFigures = null;

        if (drawing.getOutputFormats() == null ||
                drawing.getOutputFormats().size() == 0) {
            retValue = null;
        } else {
            java.util.List<Figure> toBeCopied = drawing.sort(transferFigures);
            if (toBeCopied.size() > 0) {
                try {
                    CompositeTransferable transfer = new CompositeTransferable();
                    for (OutputFormat format : drawing.getOutputFormats()) {
                        Transferable t = format.createTransferable(
                                drawing,
                                toBeCopied,
                                view.getScaleFactor());
                        if (!transfer.isDataFlavorSupported(t.getTransferDataFlavors()[0])) {
                            transfer.add(t);
                        }
                    }
                    exportedFigures = new HashSet<Figure>(transferFigures);
                    retValue = transfer;
                } catch (IOException e) {
                    if (DEBUG) {
                        e.printStackTrace();
                    }
                    retValue = null;
                }
            } else {
                retValue = null;
            }
        }

        return retValue;
    }

    @Override
    protected void exportDone(JComponent source, Transferable data, int action) {
        if (DEBUG) {
            System.out.println(this + ".exportDone " + action + " move=" + MOVE);
        }
        if (source instanceof DrawingView) {
            final DrawingView view = (DrawingView) source;
            final Drawing drawing = view.getDrawing();
            if (action == MOVE) {
                final LinkedList<CompositeFigureEvent> deletionEvents = new LinkedList<CompositeFigureEvent>();
                final LinkedList<Figure> selectedFigures = (exportedFigures == null) ? //
                        new LinkedList<Figure>() : //
                        new LinkedList<Figure>(exportedFigures);

                // Abort, if not all of the selected figures may be removed from the
                // drawing
                for (Figure f : selectedFigures) {
                    if (!f.isRemovable()) {
                        source.getToolkit().beep();
                        return;
                    }
                }

                // view.clearSelection();
                CompositeFigureListener removeListener = new CompositeFigureListener() {

                    public void areaInvalidated(CompositeFigureEvent e) {
                    }

                    public void figureAdded(CompositeFigureEvent e) {
                    }

                    public void figureRemoved(CompositeFigureEvent evt) {
                        deletionEvents.addFirst(evt);
                    }
                };
                drawing.addCompositeFigureListener(removeListener);
                drawing.removeAll(selectedFigures);
                drawing.removeCompositeFigureListener(removeListener);
                drawing.removeAll(selectedFigures);
                drawing.fireUndoableEditHappened(new AbstractUndoableEdit() {

                    @Override
                    public String getPresentationName() {
                        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels");
                        return labels.getString("edit.delete.text");
                    }

                    @Override
                    public void undo() throws CannotUndoException {
                        super.undo();
                        view.clearSelection();
                        for (CompositeFigureEvent evt : deletionEvents) {
                            drawing.add(evt.getIndex(), evt.getChildFigure());
                        }
                        view.addToSelection(selectedFigures);
                    }

                    @Override
                    public void redo() throws CannotRedoException {
                        super.redo();
                        for (CompositeFigureEvent evt : new ReversedList<CompositeFigureEvent>(deletionEvents)) {
                            drawing.remove(evt.getChildFigure());
                        }
                    }
                });
            }
        } else {
            super.exportDone(source, data, action);
        }
        exportedFigures = null;
    }

    @Override
    public void exportAsDrag(JComponent comp, InputEvent e, int action) {
        if (DEBUG) {
            System.out.println(this + ".exportAsDrag");
        }
        if (comp instanceof DrawingView) {
            DrawingView view = (DrawingView) comp;

            HashSet<Figure> transferFigures = new HashSet<Figure>();
            MouseEvent me = (MouseEvent) e;
            Figure f = view.findFigure(me.getPoint());
            if (view.getSelectedFigures().contains(f)) {
                transferFigures.addAll(view.getSelectedFigures());
            } else {
                transferFigures.add(f);
            }
            Rectangle2D.Double drawingArea = null;
            for (Figure fig : transferFigures) {
                if (drawingArea == null) {
                    drawingArea = fig.getDrawingArea();
                } else {
                    drawingArea.add(fig.getDrawingArea());
                }
            }
            Rectangle viewArea = view.drawingToView(drawingArea);
            Point imageOffset = me.getPoint();
            imageOffset.x = viewArea.x - imageOffset.x;
            imageOffset.y = viewArea.y - imageOffset.y;

            int srcActions = getSourceActions(comp);
            SwingDragGestureRecognizer recognizer = new SwingDragGestureRecognizer(new DragHandler(
                    createTransferable(view, transferFigures), imageOffset));
            recognizer.gestured(comp, me, srcActions, action);

        // XXX - What kind of drag gesture can we support for this??
        } else {
            super.exportAsDrag(comp, e, action);
        }
    }

    @Override
    public Icon getVisualRepresentation(Transferable t) {
        if (DEBUG) {
            System.out.println(this + ".getVisualRepresentation");
        }
        Image image = null;
        try {
            image = (Image) t.getTransferData(DataFlavor.imageFlavor);
        } catch (IOException ex) {
            if (DEBUG) {
                ex.printStackTrace();
            }
        } catch (UnsupportedFlavorException ex) {
            if (DEBUG) {
                ex.printStackTrace();
            }
        }

        return (image == null) ? null : new ImageIcon(image);
    }

    @Override
    public boolean canImport(JComponent comp, DataFlavor[] transferFlavors) {
        if (DEBUG) {
            System.out.println(this + ".canImport " + Arrays.asList(transferFlavors));
        }
        boolean retValue;
        if (comp instanceof DrawingView) {
            DrawingView view = (DrawingView) comp;
            Drawing drawing = view.getDrawing();

            // Search for a suitable input format
            retValue = false;
            SearchLoop:
            for (InputFormat format : drawing.getInputFormats()) {
                for (DataFlavor flavor : transferFlavors) {
                    if (flavor.isFlavorJavaFileListType() ||
                            format.isDataFlavorSupported(flavor)) {
                        retValue = true;
                        break SearchLoop;
                    }
                }
            }
        } else {
            retValue = super.canImport(comp, transferFlavors);
        }
        return retValue;
    }

    private void getDrawing() {
        throw new UnsupportedOperationException("Not yet implemented");
    }

    /**
     * This is the default drag handler for drag and drop operations that
     * use the <code>TransferHandler</code>.
     */
    private static class DragHandler implements DragGestureListener, DragSourceListener {

        private boolean scrolls;
        private Transferable transferable;
        private Point imageOffset;

        public DragHandler(Transferable t, Point imageOffset) {
            transferable = t;
            this.imageOffset = imageOffset;
        }

        // --- DragGestureListener methods -----------------------------------
        /**
         * a Drag gesture has been recognized
         */
        public void dragGestureRecognized(DragGestureEvent dge) {
            JComponent c = (JComponent) dge.getComponent();
            DefaultDrawingViewTransferHandler th = (DefaultDrawingViewTransferHandler) c.getTransferHandler();
            Transferable t = transferable;
            if (t != null) {
                scrolls = c.getAutoscrolls();
                c.setAutoscrolls(false);
                try {
//                    dge.startDrag(null, t, this);
                    Icon icon = th.getVisualRepresentation(t);
                    Image dragImage;
                    if (icon instanceof ImageIcon) {
                        dragImage = ((ImageIcon) icon).getImage();
                    } else {
                        dragImage = new BufferedImage(icon.getIconWidth(), icon.getIconHeight(), BufferedImage.TYPE_INT_ARGB);
                        Graphics g = ((BufferedImage) dragImage).createGraphics();
                        icon.paintIcon(c, g, 0, 0);
                        g.dispose();
                    }
                    dge.startDrag(null, dragImage, imageOffset, t, this);
                    return;
                } catch (RuntimeException re) {
                    c.setAutoscrolls(scrolls);
                }
            }

            th.exportDone(c, t, NONE);
        }

        // --- DragSourceListener methods -----------------------------------
        /**
         * as the hotspot enters a platform dependent drop site
         */
        public void dragEnter(DragSourceDragEvent dsde) {
        }

        /**
         * as the hotspot moves over a platform dependent drop site
         */
        public void dragOver(DragSourceDragEvent dsde) {
        }

        /**
         * as the hotspot exits a platform dependent drop site
         */
        public void dragExit(DragSourceEvent dsde) {
        }

        /**
         * as the operation completes
         */
        public void dragDropEnd(DragSourceDropEvent dsde) {
            DragSourceContext dsc = dsde.getDragSourceContext();
            JComponent c = (JComponent) dsc.getComponent();
            DefaultDrawingViewTransferHandler th = (DefaultDrawingViewTransferHandler) c.getTransferHandler();
            if (dsde.getDropSuccess()) {
                th.exportDone(c, dsc.getTransferable(), dsde.getDropAction());
            } else {
                th.exportDone(c, dsc.getTransferable(), NONE);
            }
            c.setAutoscrolls(scrolls);
        }

        public void dropActionChanged(DragSourceDragEvent dsde) {
        }
    }

    private static class SwingDragGestureRecognizer extends DragGestureRecognizer {

        SwingDragGestureRecognizer(DragGestureListener dgl) {
            super(DragSource.getDefaultDragSource(), null, NONE, dgl);
        }

        void gestured(JComponent c, MouseEvent e, int srcActions, int action) {
            setComponent(c);
            setSourceActions(srcActions);
            appendEvent(e);
            fireDragGestureRecognized(action, e.getPoint());
        }

        /**
         * register this DragGestureRecognizer's Listeners with the Component
         */
        protected void registerListeners() {
        }

        /**
         * unregister this DragGestureRecognizer's Listeners with the Component
         *
         * subclasses must override this method
         */
        protected void unregisterListeners() {
        }
    }
}
