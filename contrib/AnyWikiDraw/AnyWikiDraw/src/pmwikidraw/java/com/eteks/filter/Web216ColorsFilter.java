/*
 * @(#)Web216ColorsFilter.java   05/16/2000
 *
 * Copyright (c) 2000-2001 Emmanuel PUYBARET / eTeks <info@eteks.com>. All Rights Reserved.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 * Visit eTeks web site for up-to-date versions of this file and other
 * Java tools and tutorials : http://www.eteks.com/
 */
package com.eteks.filter;

import java.awt.image.RGBImageFilter;

/**
 * This image filter transforms the color of each pixel of an image, using
 * a fixed 216 colors palette. No special dithering is performed.<br>
 * Each Red, Green, Blue component of the 216 colors resulting palette take a value
 * among the 6 values of the following set : (0x00, 0x33, 0x66, 0x99, OxCC, OxFF).
 * 6 power 3 makes 216 total possible combinations.
 *
 * @version   1.1
 * @author    Emmanuel Puybaret
 * @since     PJA1.0
 */
public class Web216ColorsFilter extends RGBImageFilter
{
  {
    canFilterIndexColorModel = true;
  }

  /**
   * <code>RGBImageFilter</code> method implementation.
   */
  public int filterRGB (int x, int y, int rgb)
  {
    int alpha = rgb & 0xFF000000;
    int red   = (rgb & 0xFF0000) >>> 16;
    int green = (rgb & 0x00FF00) >>> 8;
    int blue  = (rgb & 0x0000FF);

    // A very poor filtering that just searchs the Web 216 closest color
    red   = red / 0x33 * 0x33 + (red % 0x33 > 0x16 ? 0x33 : 0);
    green = green / 0x33 * 0x33 + (green % 0x33 > 0x16 ? 0x33 : 0);
    blue  = blue / 0x33 * 0x33 + (blue % 0x33 > 0x16 ? 0x33 : 0);

    return alpha | (red << 16) | (green << 8) | blue;
  }
}
