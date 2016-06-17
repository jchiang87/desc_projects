create table PhosimLightCurveStats (
       sourceId BIGINT,
       meanCounts FLOAT,
       chisq FLOAT,
       dof int,
       radius FLOAT,
       xmin FLOAT,
       xmax FLOAT,
       ymin FLOAT,
       ymax FLOAT,
/*      peakCounts INT, */
       filterName CHAR(1),
       primary key (sourceId)
       )
