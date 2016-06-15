create table PhosimCentroidCounts (
       sourceId BIGINT,
       ccdVisitId BIGINT,
       numPhotons INT,
       avgX FLOAT,
       avgY FLOAT,
       primary key (sourceId, ccdVisitId)
       )
