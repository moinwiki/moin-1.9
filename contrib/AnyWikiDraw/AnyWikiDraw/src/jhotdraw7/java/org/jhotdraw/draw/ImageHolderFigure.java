/*
 * @(#)ImageHolderFigure.java
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

package org.jhotdraw.draw;

import java.awt.image.*;
import java.io.*;

/**
 * The interface of a {@link Figure} which has some editable image contents.
 * <p>
 * The {@link ImageTool} can be used to create figures which implement this
 * interface.
 *
 * <hr>
 * <b>Design Patterns</b>
 *
 * <p><em>Framework</em><br>
 * The {@code ImageTool} and the {@code ImageHolderFigure} define the
 * contracts of a smaller framework inside of the JHotDraw framework for
 * structured drawing editors.<br>
 * Contract: {@link ImageHolderFigure}, {@link ImageTool}.
 *
 * <p><em>Prototype</em><br>
 * The {@code ImageTool} creates new figures by cloning a prototype
 * {@code ImageHolderFigure} object.<br>
 * Prototype: {@link ImageHolderFigure}; Client: {@link ImageTool}.
 * <hr>
 *
 * @author Werner Randelshofer
 * @version $Id: ImageHolderFigure.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public interface ImageHolderFigure extends Figure {
    /**
     * Loads an image from a File.
     * By convention this method is never invoked on the AWT Event Dispatcher 
     * Thread.
     */
    public void loadImage(File f) throws IOException;
    /**
     * Loads an image from an Input Stream.
     * By convention this method is never invoked on the AWT Event Dispatcher 
     * Thread.
     */
    public void loadImage(InputStream in) throws IOException;
    /**
     * Gets the buffered image from the figure.
     */
    public BufferedImage getBufferedImage();
    /**
     * Sets the buffered image for the figure.
     */
    public void setBufferedImage(BufferedImage image);
    
    /**
     * Sets the image.
     *
     * @param imageData The image data. If this is null, a buffered image must
     * be provided.
     * @param bufferedImage An image constructed from the imageData. If this
     * is null, imageData must be provided.
     */
    public void setImage(byte[] imageData, BufferedImage bufferedImage) throws IOException;
    /**
     * Gets the image data.
     *
     * @return imageData The image data, or null, if the ImageHolderFigure does
     * not have an image.
     */
    public byte[] getImageData();

}
