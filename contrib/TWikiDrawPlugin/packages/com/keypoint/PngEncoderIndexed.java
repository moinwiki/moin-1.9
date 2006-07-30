package com.keypoint;

import java.awt.Image;
import java.awt.image.ImageObserver;
import java.awt.image.PixelGrabber;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.zip.CRC32;
import java.util.zip.Deflater;
import java.util.zip.DeflaterOutputStream;
import java.util.*;
import java.io.*;

/**
 * PngEncoder takes a Java Image object and creates a byte string which can be saved as a PNG file.
 * The Image is presumed to use the DirectColorModel.
 *
 * <p>Thanks to Jay Denny at KeyPoint Software
 *    http://www.keypoint.com/
 * who let me develop this code on company time.</p>
 *
 * <p>You may contact me with (probably very-much-needed) improvements,
 * comments, and bug fixes at:</p>
 *
 *   <p><code>david@catcode.com</code></p>
 *
 * <p>This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.</p>
 *
 * <p>This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.</p>
 *
 * <p>You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 * A copy of the GNU LGPL may be found at
 * <code>http://www.gnu.org/copyleft/lesser.html</code></p>
 *
 * @author J. David Eisenberg
 * @version 1.5, 19 Oct 2003
 *
 * CHANGES:
 * --------
 * 19-Nov-2002 : CODING STYLE CHANGES ONLY (by David Gilbert for Object Refinery Limited);
 * 19-Sep-2003 : Fix for platforms using EBCDIC (contributed by Paulo Soares);
 * 19-Oct-2003 : Change private fields to protected fields so that
 *               PngEncoderB can inherit them (JDE)
 *				 Fixed bug with calculation of nRows
 */

public class PngEncoderIndexed extends Object {

    /** IHDR tag. */
    protected static final byte IHDR[] = {73, 72, 68, 82};
    
    /** PLTE tag. */
    protected static final byte PLTE[] = {80, 76, 84, 69};

    /** tRNS tag. */
    protected static final byte tRNS[] = {116, 82, 78, 83};

    /** IDAT tag. */
    protected static final byte IDAT[] = {73, 68, 65, 84};
    
    /** IEND tag. */
    protected static final byte IEND[] = {73, 69, 78, 68};

	protected static final int DEFAULT_COMPRESSION = 5;

    /** The png bytes. */
    protected byte[] pngBytes;

    /** The image. */
    protected Image image;

    /** The width. */
    protected int width, height;

    /** The byte position. */
    protected int bytePos, maxPos;

    /** CRC. */
    protected CRC32 crc = new CRC32();

    /** The CRC value. */
    protected long crcValue;

    /** The compression level. */
    protected int compressionLevel;

    /**
     * Class constructor
     */
    public PngEncoderIndexed() {
        this(null, DEFAULT_COMPRESSION);
    }

    /**
     * Class constructor specifying Image to encode, with no alpha channel encoding.
     *
     * @param image A Java Image object which uses the DirectColorModel
     * @see java.awt.Image
     */
    public PngEncoderIndexed(Image image) {
        this(image, DEFAULT_COMPRESSION);
    }

    /**
     * Class constructor specifying Image source to encode, 
	 * and compression level.
     *
     * @param image A Java Image object
     * @param compLevel 0..9
     * @see java.awt.Image
     */
    public PngEncoderIndexed(Image image, int compLevel) {
        this.image = image;
        if (compLevel >= 0 && compLevel <= 9) {
            this.compressionLevel = compLevel;
        }
    }

    /**
     * Set the image to be encoded
     *
     * @param image A Java Image object which uses the DirectColorModel
     * @see java.awt.Image
     * @see java.awt.image.DirectColorModel
     */
    public void setImage(Image image) {
        this.image = image;
        pngBytes = null;
    }

    /**
     * Creates an array of bytes that is the PNG equivalent of the current image
     *
     * @return an array of bytes, or null if there was a problem
     */
    public byte[] pngEncode() {
        byte[]  pngIdBytes = {-119, 80, 78, 71, 13, 10, 26, 10};

        if (image == null) {
            return null;
        }
        width = image.getWidth(null);
        height = image.getHeight(null);

        /*
         * start with an array that is big enough to hold all the pixels
         * (plus filter bytes), and an extra 200 bytes for header info
         */
        pngBytes = new byte[((width + 1) * height * 3) + 200];

        /*
         * keep track of largest byte written to the array
         */
        maxPos = 0;

        bytePos = writeBytes(pngIdBytes, 0);
        //hdrPos = bytePos;
        writeHeader();
        //dataPos = bytePos;
        if (writeImageData()) {
            writeEnd();
            pngBytes = resizeByteArray(pngBytes, maxPos);
        }
        else {
            pngBytes = null;
        }
        return pngBytes;
    }

    /**
     * Set the compression level to use
     *
     * @param level 0 through 9
     */
    public void setCompressionLevel(int level) {
        if (level >= 0 && level <= 9) {
            this.compressionLevel = level;
        }
    }

    /**
     * Retrieve compression level
     *
     * @return int in range 0-9
     */
    public int getCompressionLevel() {
        return compressionLevel;
    }

    /**
     * Increase or decrease the length of a byte array.
     *
     * @param array The original array.
     * @param newLength The length you wish the new array to have.
     * @return Array of newly desired length. If shorter than the
     *         original, the trailing elements are truncated.
     */
    protected byte[] resizeByteArray(byte[] array, int newLength) {
        byte[]  newArray = new byte[newLength];
        int     oldLength = array.length;

        System.arraycopy(array, 0, newArray, 0, Math.min(oldLength, newLength));
        return newArray;
    }

    /**
     * Write an array of bytes into the pngBytes array.
     * Note: This routine has the side effect of updating
     * maxPos, the largest element written in the array.
     * The array is resized by 1000 bytes or the length
     * of the data to be written, whichever is larger.
     *
     * @param data The data to be written into pngBytes.
     * @param offset The starting point to write to.
     * @return The next place to be written to in the pngBytes array.
     */
    protected int writeBytes(byte[] data, int offset) {
        maxPos = Math.max(maxPos, offset + data.length);
        if (data.length + offset > pngBytes.length) {
            pngBytes = resizeByteArray(pngBytes, pngBytes.length + Math.max(1000, data.length));
        }
        System.arraycopy(data, 0, pngBytes, offset, data.length);
        return offset + data.length;
    }

    /**
     * Write an array of bytes into the pngBytes array, specifying number of bytes to write.
     * Note: This routine has the side effect of updating
     * maxPos, the largest element written in the array.
     * The array is resized by 1000 bytes or the length
     * of the data to be written, whichever is larger.
     *
     * @param data The data to be written into pngBytes.
     * @param nBytes The number of bytes to be written.
     * @param offset The starting point to write to.
     * @return The next place to be written to in the pngBytes array.
     */
    protected int writeBytes(byte[] data, int nBytes, int offset) {
        maxPos = Math.max(maxPos, offset + nBytes);
        if (nBytes + offset > pngBytes.length) {
            pngBytes = resizeByteArray(pngBytes, pngBytes.length + Math.max(1000, nBytes));
        }
        System.arraycopy(data, 0, pngBytes, offset, nBytes);
        return offset + nBytes;
    }

    /**
     * Write a two-byte integer into the pngBytes array at a given position.
     *
     * @param n The integer to be written into pngBytes.
     * @param offset The starting point to write to.
     * @return The next place to be written to in the pngBytes array.
     */
    protected int writeInt2(int n, int offset) {
        byte[] temp = {(byte) ((n >> 8) & 0xff), (byte) (n & 0xff)};
        return writeBytes(temp, offset);
    }

    /**
     * Write a four-byte integer into the pngBytes array at a given position.
     *
     * @param n The integer to be written into pngBytes.
     * @param offset The starting point to write to.
     * @return The next place to be written to in the pngBytes array.
     */
    protected int writeInt4(int n, int offset) {
        byte[] temp = {(byte) ((n >> 24) & 0xff),
                       (byte) ((n >> 16) & 0xff),
                       (byte) ((n >> 8) & 0xff),
                       (byte) (n & 0xff)};
        return writeBytes(temp, offset);
    }

    /**
     * Write a single byte into the pngBytes array at a given position.
     *
     * @param b The integer to be written into pngBytes.
     * @param offset The starting point to write to.
     * @return The next place to be written to in the pngBytes array.
     */
    protected int writeByte(int b, int offset) {
        byte[] temp = {(byte) b};
        return writeBytes(temp, offset);
    }

    /**
     * Write a PNG "IHDR" chunk into the pngBytes array.
     */
    protected void writeHeader() {
        int startPos;

        startPos = bytePos = writeInt4(13, bytePos);
        bytePos = writeBytes(IHDR, bytePos);
        width = image.getWidth(null);
        height = image.getHeight(null);
        bytePos = writeInt4(width, bytePos);
        bytePos = writeInt4(height, bytePos);
        bytePos = writeByte(8, bytePos); // bit depth
        bytePos = writeByte(3, bytePos); // palette
        bytePos = writeByte(0, bytePos); // compression method
        bytePos = writeByte(0, bytePos); // filter method
        bytePos = writeByte(0, bytePos); // no interlace
        crc.reset();
        crc.update(pngBytes, startPos, bytePos - startPos);
        crcValue = crc.getValue();
        bytePos = writeInt4((int) crcValue, bytePos);
    }

    /**
     * Write the image data into the pngBytes array.
     * This will write one or more PNG "IDAT" chunks. In order
     * to conserve memory, this method grabs as many rows as will
     * fit into 32K bytes, or the whole image; whichever is less.
     *
     *
     * @return true if no errors; false if error grabbing pixels
     */
    protected boolean writeImageData() {
        int rowsLeft;  // number of rows remaining to write
        int startRow;       // starting row to process this time through
        int nRows;              // how many rows to grab at a time

        byte[] scanLines;       // the scan lines to be compressed
        int scanPos;            // where we are in the scan lines
        int startPos;           // where this line's actual pixels start (used for filtering)

        byte[] compressedLines; // the resultant compressed lines
        int nCompressed;        // how big is the compressed area?

        //int depth;              // color depth ( handle only 8 or 32 )

		// palette without transparency (TWikiDrawPlugin does not need it)
		Acme.IntHashtable palette = new Acme.IntHashtable();
		PngEncoderHashitem item;
		int paletteIndex = 0, transIndex = -1, transRGBA = 0;

        PixelGrabber pg;

        Deflater scrunch = new Deflater(compressionLevel);
        ByteArrayOutputStream outBytes = new ByteArrayOutputStream(1024);

        DeflaterOutputStream compBytes = new DeflaterOutputStream(outBytes, scrunch);
        try {
			/*
			 * create palette for image
			 */
			rowsLeft = height;
			startRow = 0;
            while (rowsLeft > 0) {
                nRows = Math.min(64000 / (width * 4), rowsLeft);
                nRows = Math.max(nRows, 1);

                int[] pixels = new int[width * nRows];

                pg = new PixelGrabber(image, 0, startRow, width, nRows,
									  pixels, 0, width);
                try {
                    pg.grabPixels();
                }
                catch (Exception e) {
                    System.err.println("interrupted waiting for pixels!");
                    return false;
                }
                if ((pg.getStatus() & ImageObserver.ABORT) != 0) {
                    System.err.println("image fetch aborted or errored");
                    return false;
                }

                scanPos = 0;
                startPos = 1;
                for (int i = 0; i < width * nRows; i++) {
					int rgba = pixels[i];
					item = (PngEncoderHashitem) palette.get( rgba );
					if (item == null) {
						if (paletteIndex >= 256)
							throw new IOException("too many colors for a PNG");
						item = new PngEncoderHashitem(rgba, 1, paletteIndex, false);
						palette.put( rgba, item );
						++paletteIndex;
					} else
						++item.count;
                }

                startRow += nRows;
                rowsLeft -= nRows;
            }

			/*
			 * write PLTE chunk
			 */
            crc.reset();
            bytePos = writeInt4(paletteIndex * 3, bytePos); // length
            bytePos = writeBytes(PLTE, bytePos);            // magic
            crc.update(PLTE);
			// write palette data
			byte[] pltedata = new byte[paletteIndex * 3];
			for (Enumeration e = palette.elements(); e.hasMoreElements();) {
				item = (PngEncoderHashitem) e.nextElement();
				pltedata[item.index*3]=(byte) ((item.rgba>>16)&0xff);
				pltedata[item.index*3+1]=(byte) ((item.rgba>> 8)&0xff);
				pltedata[item.index*3+2]=(byte) ( item.rgba     &0xff);
			}
			bytePos = writeBytes(pltedata, bytePos);
			crc.update(pltedata);
			// add crc
            crcValue = crc.getValue();
            bytePos = writeInt4((int) crcValue, bytePos);
			
			/*
			 * create scanline with palette indices
			 */
			rowsLeft = height;
			startRow = 0;
            while (rowsLeft > 0) {
                nRows = Math.min(64000 / (width * 4), rowsLeft);
                nRows = Math.max(nRows, 1);

                int[] pixels = new int[width * nRows];

                pg = new PixelGrabber(image, 0, startRow,
                    width, nRows, pixels, 0, width);
                try {
                    pg.grabPixels();
                }
                catch (Exception e) {
                    System.err.println("interrupted waiting for pixels!");
                    return false;
                }
                if ((pg.getStatus() & ImageObserver.ABORT) != 0) {
                    System.err.println("image fetch aborted or errored");
                    return false;
                }

                /*
                 * Create a data chunk. scanLines adds "nRows" for
                 * the filter bytes.
                 */
                scanLines = new byte[width * nRows + nRows];
				
                scanPos = 0;
                startPos = 1;
                for (int i = 0; i < width * nRows; i++) {
                    if (i % width == 0) {
                        scanLines[scanPos++] = (byte) 0; /* no filter */
                        startPos = scanPos;
                    }
					item = (PngEncoderHashitem) palette.get( pixels[i] );
					if (item == null)
						throw new IOException( "color not found" );
					scanLines[scanPos++] = (byte) item.index;
                }
				
                /*
                 * Write these lines to the output area
                 */
                compBytes.write(scanLines, 0, scanPos);
				
                startRow += nRows;
                rowsLeft -= nRows;
            }
            compBytes.close();
			
            /*
             * Write the compressed bytes
             */
            compressedLines = outBytes.toByteArray();
            nCompressed = compressedLines.length;

            crc.reset();
            bytePos = writeInt4(nCompressed, bytePos);
            bytePos = writeBytes(IDAT, bytePos);
            crc.update(IDAT);
            bytePos = writeBytes(compressedLines, nCompressed, bytePos);
            crc.update(compressedLines, 0, nCompressed);

            crcValue = crc.getValue();
            bytePos = writeInt4((int) crcValue, bytePos);
            scrunch.finish();
            return true;
        }
        catch (IOException e) {
            System.err.println(e.toString());
            return false;
        }
    }

    /**
     * Write a PNG "IEND" chunk into the pngBytes array.
     */
    protected void writeEnd() {
        bytePos = writeInt4(0, bytePos);
        bytePos = writeBytes(IEND, bytePos);
        crc.reset();
        crc.update(IEND);
        crcValue = crc.getValue();
        bytePos = writeInt4((int) crcValue, bytePos);
    }

}

class PngEncoderHashitem {
	
    public int rgba;
    public int count;
    public int index;
    public boolean isTrans;
	
    public PngEncoderHashitem(int rgba, int count, int index, boolean isTrans) {
		this.rgba = rgba;
		this.count = count;
		this.index = index;
		this.isTrans = isTrans;
	}
}
