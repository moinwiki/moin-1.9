/*
 * @(#)InputStreamTransferable.java
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

package org.jhotdraw.gui.datatransfer;

import java.awt.datatransfer.*;
import java.io.*;

/**
 * A Transferable with an InputStream as its transfer class.
 *
 * @author Werner Randelshofer
 * @version $Id: InputStreamTransferable.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class InputStreamTransferable extends AbstractTransferable {
    private byte[] data;
    
    /** Creates a new instance. */
    public InputStreamTransferable(DataFlavor flavor, byte[] data) {
        this(new DataFlavor[] { flavor }, data);
    }
    public InputStreamTransferable(DataFlavor[] flavors, byte[] data) {
        super(flavors);
        this.data = data;
    }

    public Object getTransferData(DataFlavor flavor) throws UnsupportedFlavorException, IOException {
        if (! isDataFlavorSupported(flavor)) {
            throw new UnsupportedFlavorException(flavor);
        }
        return new ByteArrayInputStream(data);
    }
}
