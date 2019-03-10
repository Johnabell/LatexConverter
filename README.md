# LatexConverter

Converts latex to OMML.

## Examples:
<table>
    <tr>
        <th> Latex </th>
        <th> OMML </th>
    </tr>
    <tr>
        <td>
            <pre lang="latex">
\begin{align*} 
    \int_{-\infity}^\infty e^{-x^2} dx = \sqrt{\pi}
\end{align*}
            </pre>
        </td>
        <td>
            <pre lang='xml'>
    
<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:mml="http://www.w3.org/1998/Math/MathML">
  <m:eqArr>
    <m:e>
      <m:nary>
        <m:naryPr>
          <m:chr m:val="∫"/>
          <m:limLoc m:val="subSup"/>
          <m:grow m:val="1"/>
          <m:subHide m:val="off"/>
          <m:supHide m:val="off"/>
        </m:naryPr>
        <m:sub>
          <m:r>
            <m:t>−</m:t>
          </m:r>
          <m:r>
            <m:rPr>
              <m:sty m:val="p"/>
            </m:rPr>
            <m:t>infity</m:t>
          </m:r>
        </m:sub>
        <m:sup>
          <m:r>
            <m:t>∞</m:t>
          </m:r>
        </m:sup>
        <m:e/>
      </m:nary>
      <m:sSup>
        <m:e>
          <m:r>
            <m:t>e</m:t>
          </m:r>
        </m:e>
        <m:sup>
          <m:r>
            <m:t>−</m:t>
          </m:r>
          <m:sSup>
            <m:e>
              <m:r>
                <m:t>x</m:t>
              </m:r>
            </m:e>
            <m:sup>
              <m:r>
                <m:t>2</m:t>
              </m:r>
            </m:sup>
          </m:sSup>
        </m:sup>
      </m:sSup>
      <m:r>
        <m:t>dx=</m:t>
      </m:r>
      <m:rad>
        <m:radPr>
          <m:degHide m:val="on"/>
        </m:radPr>
        <m:deg/>
        <m:e>
          <m:r>
            <m:t>π</m:t>
          </m:r>
        </m:e>
      </m:rad>
    </m:e>
  </m:eqArr>
</m:oMath>
            </pre>
        </td>
    </tr>
    <tr>
        <td>
            <pre lang='latex'>
\begin{bmatrix}
    a_{1,1} & a_{1,2} & \cdots & a_{1,n} \\\\
    a_{2,1} & a_{2,2} & \cdots & a_{2,n} \\\\
    \vdots  & \vdots  & \ddots & \vdots \\\\
    a_{m,1} & a_{m,2} & \cdots & a_{m,n} 
\end{bmatrix}
            </pre>
        </td>
        <td>
            <pre lang='xml'>
    

<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:mml="http://www.w3.org/1998/Math/MathML">
  <m:d>
    <m:dPr>
      <m:begChr m:val="["/>
      <m:sepChr m:val=""/>
      <m:endChr m:val="]"/>
    </m:dPr>
    <m:e>
      <m:m>
        <m:mPr>
          <m:baseJc m:val="center"/>
          <m:plcHide m:val="on"/>
          <m:mcs>
            <m:mc>
              <m:mcPr>
                <m:count m:val="4"/>
                <m:mcJc m:val="center"/>
              </m:mcPr>
            </m:mc>
          </m:mcs>
        </m:mPr>
        <m:mr>
          <m:e>
            <m:sSub>
              <m:e>
                <m:r>
                  <m:t>a</m:t>
                </m:r>
              </m:e>
              <m:sub>
                <m:r>
                  <m:t>1,1</m:t>
                </m:r>
              </m:sub>
            </m:sSub>
          </m:e>
          <m:e>
            <m:sSub>
              <m:e>
                <m:r>
                  <m:t>a</m:t>
                </m:r>
              </m:e>
              <m:sub>
                <m:r>
                  <m:t>1,2</m:t>
                </m:r>
              </m:sub>
            </m:sSub>
          </m:e>
          <m:e>
            <m:r>
              <m:t>⋯</m:t>
            </m:r>
          </m:e>
          <m:e>
            <m:sSub>
              <m:e>
                <m:r>
                  <m:t>a</m:t>
                </m:r>
              </m:e>
              <m:sub>
                <m:r>
                  <m:t>1,n</m:t>
                </m:r>
              </m:sub>
            </m:sSub>
          </m:e>
        </m:mr>
        <m:mr>
          <m:e>
            <m:sSub>
              <m:e>
                <m:r>
                  <m:t>a</m:t>
                </m:r>
              </m:e>
              <m:sub>
                <m:r>
                  <m:t>2,1</m:t>
                </m:r>
              </m:sub>
            </m:sSub>
          </m:e>
          <m:e>
            <m:sSub>
              <m:e>
                <m:r>
                  <m:t>a</m:t>
                </m:r>
              </m:e>
              <m:sub>
                <m:r>
                  <m:t>2,2</m:t>
                </m:r>
              </m:sub>
            </m:sSub>
          </m:e>
          <m:e>
            <m:r>
              <m:t>⋯</m:t>
            </m:r>
          </m:e>
          <m:e>
            <m:sSub>
              <m:e>
                <m:r>
                  <m:t>a</m:t>
                </m:r>
              </m:e>
              <m:sub>
                <m:r>
                  <m:t>2,n</m:t>
                </m:r>
              </m:sub>
            </m:sSub>
          </m:e>
        </m:mr>
        <m:mr>
          <m:e>
            <m:r>
              <m:t>⋮</m:t>
            </m:r>
          </m:e>
          <m:e>
            <m:r>
              <m:t>⋮</m:t>
            </m:r>
          </m:e>
          <m:e>
            <m:r>
              <m:t>⋱</m:t>
            </m:r>
          </m:e>
          <m:e>
            <m:r>
              <m:t>⋮</m:t>
            </m:r>
          </m:e>
        </m:mr>
        <m:mr>
          <m:e>
            <m:sSub>
              <m:e>
                <m:r>
                  <m:t>a</m:t>
                </m:r>
              </m:e>
              <m:sub>
                <m:r>
                  <m:t>m,1</m:t>
                </m:r>
              </m:sub>
            </m:sSub>
          </m:e>
          <m:e>
            <m:sSub>
              <m:e>
                <m:r>
                  <m:t>a</m:t>
                </m:r>
              </m:e>
              <m:sub>
                <m:r>
                  <m:t>m,2</m:t>
                </m:r>
              </m:sub>
            </m:sSub>
          </m:e>
          <m:e>
            <m:r>
              <m:t>⋯</m:t>
            </m:r>
          </m:e>
          <m:e>
            <m:sSub>
              <m:e>
                <m:r>
                  <m:t>a</m:t>
                </m:r>
              </m:e>
              <m:sub>
                <m:r>
                  <m:t>m,n</m:t>
                </m:r>
              </m:sub>
            </m:sSub>
          </m:e>
        </m:mr>
      </m:m>
    </m:e>
  </m:d>
</m:oMath>
            </pre>
        </td>
    </tr>
</table>
