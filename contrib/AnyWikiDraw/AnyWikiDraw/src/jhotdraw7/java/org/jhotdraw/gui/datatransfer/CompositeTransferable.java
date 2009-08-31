/*
 * @(#)CompositeTransferable.java
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

package org.jhotdraw.gui.datatransfer;

import java.awt.datatransfer.*;
import java.util.*;
import java.io.*;
/**
 *
 *
 * @author  Werner Randelshofer
 */
public class CompositeTransferable implements Transferable, ClipboardOwner {
    private HashMap<DataFlavor,Transferable> transferables = new HashMap<DataFlavor,Transferable>();
    private LinkedList<DataFlavor> flavors = new LinkedList<DataFlavor>();
    
    /** Creates a new instance of CompositeTransferable */
    public CompositeTransferable() {
    }
    
    public void add(Transferable t) {
        DataFlavor[] f = t.getTransferDataFlavors();
        for (int i=0; i < f.length; i++) {
            if (! transferables.containsKey(f[i])) flavors.add(f[i]);
            transferables.put(f[i], t);
            
        }
    }
    
    /**
     * Returns an object which represents the data to be transferred.  The class
     * of the object returned is defined by the representation class of the flavor.
     *
     * @param flavor the requested flavor for the data
     * @see DataFlavor#getRepresentationClass
     * @exception IOException                if the data is no longer available
     *             in the requested flavor.
     * @exception UnsupportedFlavorException if the requested data flavor is
     *             not supported.
     */
    public Object getTransferData(DataFlavor flavor) throws UnsupportedFlavorException, IOException {
        Transferable t = (Transferable) transferables.get(flavor);
        if (t == null) throw new UnsupportedFlavorException(flavor);
        return t.getTransferData(flavor);
    }
    
    /**
     * Returns an array of DataFlavor objects indicating the flavors the data
     * can be provided in.  The array should be ordered according to preference
     * for providing the data (from most richly descriptive to least descriptive).
     * @return an array of data flavors in which this data can be transferred
     */
    public DataFlavor[] getTransferDataFlavors() {
        return (DataFlavor[]) flavors.toArray(new DataFlavor[transferables.size()]);
    }
    
    /**
     * Returns whether or not the specified data flavor is supported for
     * this object.
     * @param flavor the requested flavor for the data
     * @return boolean indicating wjether or not the data flavor is supported
     */
    public boolean isDataFlavorSupported(DataFlavor flavor) {
        return transferables.containsKey(flavor);
    }

    public void lostOwnership(Clipboard clipboard, Transferable contents) {
    }
}
