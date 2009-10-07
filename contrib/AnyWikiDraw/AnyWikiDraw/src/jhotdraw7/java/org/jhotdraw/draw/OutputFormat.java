/*
 * @(#)OutputFormat.java
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

import java.awt.datatransfer.*;
import java.io.*;
import java.util.*;
import javax.swing.*;

/**
 * An <em>output format</em> implements a strategy for writing a {@link Drawing}
 * using a specific encoding into an {@code OutputStream}, a {@code File} or a
 * {@code Transferable}.
 * <p>
 * Typically an encoding can be recognized by a Mime type or by a file extension.
 * To identify the encoding used by a file, an appropriate {@code FileFilter}
 * for a javax.swing.JFileChooser component can be requested from {@code OutputFormat}.
 * <p>
 * This interface intentionally contains many identical operations like
 * InputFormat to make it easy, to write classes that implement both interfaces.
 *
 * <hr>
 * <b>Design Patterns</b>
 *
 * <p><em>Strategy</em><br>
 * {@code OutputFormat} encapsulates a strategy for writing drawings to output
 * streams.<br>
 * Strategy: {@link OutputFormat}; Context: {@link Drawing}.
 * <hr>
 *
 * @author Werner Randelshofer
 * @version $Id: OutputFormat.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public interface OutputFormat {
    /**
     * Return a FileFilter that can be used to identify files which can be stored 
     * with this output format. Typically, each output format has its own
     * recognizable file extension.
     *
     * @return FileFilter to be used with a javax.swing.JFileChooser
     */
    public javax.swing.filechooser.FileFilter getFileFilter();

    /**
     * Returns the file extension for the output format.
     * The file extension should be appended to a file name when storing a
     * Drawing with the specified file format.
     */
    public String getFileExtension();
    
    /**
     * Return a JFileChooser accessory that can be used to customize the output
     * format.
     *
     * @return A JFileChooser accessory to be used with a javax.swing.JFileChooser
     * Returns null, if no accessory is provided for this format.
     */
    public JComponent getOutputFormatAccessory();
    
    /**
     * Writes a Drawing into a file.
     *
     * @param file The file.
     * @param drawing The drawing.
     */
    public void write(File file, Drawing drawing) throws IOException;

    /**
     * Writes a Drawing into an output stream.
     *
     * @param out The output stream.
     * @param drawing The drawing.
     */
    public void write(OutputStream out, Drawing drawing) throws IOException;
    
    /**
     * Creates a Transferable for the specified list of Figures.
     *
     * @param drawing The drawing.
     * @param figures A list of figures of the drawing.
     * @param scaleFactor The factor to be used, when the Transferable creates
     * an image with a fixed size from the figures.
     * @return The Transferable.
     */
    public Transferable createTransferable(Drawing drawing, List<Figure> figures, double scaleFactor) throws IOException;
}
