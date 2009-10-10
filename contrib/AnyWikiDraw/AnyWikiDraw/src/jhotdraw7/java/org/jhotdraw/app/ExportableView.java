/*
 * @(#)ExportableView.java
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

package org.jhotdraw.app;

import java.awt.*;
import java.io.*;
import javax.swing.*;

/**
 * The interface of a {@link View} which can export its document.
 *
 * <hr>
 * <b>Design Patterns</b>
 *
 * <p><em>Framework</em><br>
 * The interfaces and classes listed below define together the contracts
 * of a smaller framework inside of the JHotDraw framework for document oriented
 * applications.<br>
 * Contract: {@link ExportableView}, {@link org.jhotdraw.app.action.ExportAction}.
 * <hr>
 *
 * @author Werner Randelshofer
 * @version $Id: ExportableView.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public interface ExportableView extends View {
    /**
     * Gets the file chooser for exporting the view.
     */
  public JFileChooser getExportChooser();
 
  /**
   * Exports the view. 
   * By convention this method is never invoked on the AWT Event Dispatcher Thread. 
   *
   * @param f The file to which export the view.
   * @param filter The FileFilter that was used to choose the file. This can be null.
   * @param accessory The Accessory used by the JFileChooser. This can be null.
   */
  public void export(File f, javax.swing.filechooser.FileFilter filter, Component accessory) throws IOException;
}
