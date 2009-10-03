/*
 * @(#)ImageTool.java
 *
 * Copyright (c) 1996-2008 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and
 * contributors of the JHotDraw project ("the copyright holders").
 * You may not use, copy or modify this software, except in
 * accordance with the license agreement you entered into with
 * the copyright holders. For details see accompanying license terms.
 */
package org.jhotdraw.samples.svg;

import org.jhotdraw.draw.*;
import java.io.*;
import javax.swing.*;
import java.awt.*;
import java.util.*;
import org.jhotdraw.gui.Worker;
import org.jhotdraw.samples.svg.io.SVGInputFormat;
import org.jhotdraw.samples.svg.io.SVGZInputFormat;

/**
 * A tool to create new figures from an input file. If the file holds a bitmap
 * image, this tool creates a SVGImageFigure. If the file holds a SVG or a SVGZ
 * image, ths tool creates a SVGGroupFigure.
 * <p>
 * Immediately, after the ImageTool has been activated, it opens a JFileChooser,
 * letting the user specify a file. The the user then performs
 * the following mouse gesture:
 * <ol>
 * <li>Press the mouse button and drag the mouse over the DrawingView.
 * This defines the bounds of the created Figure.</li>
 * </ol>
 *
 * @author Werner Randelshofer
 * @version $Id: SVGCreateFromFileTool.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class SVGCreateFromFileTool extends CreationTool {

    protected FileDialog fileDialog;
    protected JFileChooser fileChooser;
    protected Thread workerThread;
    protected CompositeFigure groupPrototype;
    protected ImageHolderFigure imagePrototype;
    protected boolean useFileDialog;

    /** Creates a new instance. */
    public SVGCreateFromFileTool(ImageHolderFigure imagePrototype, CompositeFigure groupPrototype) {
        super(imagePrototype);
        this.groupPrototype = groupPrototype;
        this.imagePrototype = imagePrototype;
    }

    /** Creates a new instance. */
    public SVGCreateFromFileTool(ImageHolderFigure imagePrototype, CompositeFigure groupPrototype, Map<AttributeKey, Object> attributes) {
        super(imagePrototype, attributes);
        this.groupPrototype = groupPrototype;
        this.imagePrototype = imagePrototype;
    }

    public void setUseFileDialog(boolean newValue) {
        useFileDialog = newValue;
        if (useFileDialog) {
            fileChooser = null;
        } else {
            fileDialog = null;
        }
    }

    public boolean isUseFileDialog() {
        return useFileDialog;
    }
    @Override
    public void activate(DrawingEditor editor) {
        super.activate(editor);

        if (workerThread != null) {
            try {
                workerThread.join();
            } catch (InterruptedException ex) {
                // ignore
            }
        }

        final File file;
        if (useFileDialog) {
           getFileDialog().setVisible(true);
           if (getFileDialog().getFile() != null) {
                file = new File(getFileDialog().getDirectory(), getFileDialog().getFile());
            } else {
                file = null;
            }
        } else {
            if (getFileChooser().showOpenDialog(getView().getComponent()) == JFileChooser.APPROVE_OPTION) {
                file = getFileChooser().getSelectedFile();
            } else {
                file = null;
            }
        }

        if (file != null) {
            Worker worker;

            if (file.getName().toLowerCase().endsWith(".svg") ||
                    file.getName().toLowerCase().endsWith(".svgz")) {
                prototype = ((Figure) groupPrototype.clone());
                worker = new Worker() {

                    public Object construct() {
                        Drawing drawing = new DefaultDrawing();
                        try {
                            InputFormat in = (file.getName().toLowerCase().endsWith(".svg")) ? new SVGInputFormat() : new SVGZInputFormat();
                            in.read(file, drawing);
                        } catch (Throwable t) {
                            return t;
                        }
                        return drawing;
                    }

                    public void finished(Object value) {
                        if (value instanceof Throwable) {
                            Throwable t = (Throwable) value;
                            JOptionPane.showMessageDialog(getView().getComponent(),
                                    t.getMessage(),
                                    null,
                                    JOptionPane.ERROR_MESSAGE);
                            getDrawing().remove(createdFigure);
                            fireToolDone();
                        } else {
                            Drawing drawing = (Drawing) value;
                            CompositeFigure parent;
                            if (createdFigure == null) {
                                parent = (CompositeFigure) prototype;
                                for (Figure f : drawing.getChildren()) {
                                    parent.basicAdd(f);
                                }
                            } else {
                                parent = (CompositeFigure) createdFigure;
                                parent.willChange();
                                for (Figure f : drawing.getChildren()) {
                                    parent.add(f);
                                }
                                parent.changed();
                            }
                        }
                    }
                };
            } else {
                prototype = imagePrototype;
                final ImageHolderFigure loaderFigure = ((ImageHolderFigure) prototype.clone());
                worker = new Worker() {

                    public Object construct() {
                        try {
                            ((ImageHolderFigure) loaderFigure).loadImage(file);
                        } catch (Throwable t) {
                            return t;
                        }
                        return null;
                    }

                    public void finished(Object value) {
                        if (value instanceof Throwable) {
                            Throwable t = (Throwable) value;
                            JOptionPane.showMessageDialog(getView().getComponent(),
                                    t.getMessage(),
                                    null,
                                    JOptionPane.ERROR_MESSAGE);
                            getDrawing().remove(createdFigure);
                            fireToolDone();
                        } else {
                            try {
                                if (createdFigure == null) {
                                    ((ImageHolderFigure) prototype).setImage(loaderFigure.getImageData(), loaderFigure.getBufferedImage());
                                } else {
                                    ((ImageHolderFigure) createdFigure).setImage(loaderFigure.getImageData(), loaderFigure.getBufferedImage());
                                }
                            } catch (IOException ex) {
                                JOptionPane.showMessageDialog(getView().getComponent(),
                                        ex.getMessage(),
                                        null,
                                        JOptionPane.ERROR_MESSAGE);
                            }
                        }
                    }
                };
            }
            workerThread = new Thread(worker);
            workerThread.start();
        } else {
            //getDrawing().remove(createdFigure);
            if (isToolDoneAfterCreation()) {
                fireToolDone();
            }
        }
    }

    protected Figure createFigure() {
        if (prototype instanceof CompositeFigure) {
            // we must not apply default attributs to the composite figure,
            // because this would change the look of the figures that we
            // read from the SVG file.
            return (Figure) prototype.clone();
        } else {
            return super.createFigure();
        }
    }

    private JFileChooser getFileChooser() {
        if (fileChooser == null) {
            fileChooser = new JFileChooser();
        }
        return fileChooser;
    }

    private FileDialog getFileDialog() {
        if (fileDialog == null) {
            fileDialog = new FileDialog(new Frame());
        }
        return fileDialog;
    }
}
