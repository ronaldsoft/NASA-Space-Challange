-- =============================================================================
-- SEMILLA MOCK — no son mediciones de MOLA, LOLA ni Copernicus DEM GLO-90
-- La lista de validación es PROVISIONAL hasta que Expertos entregue la oficial.
-- =============================================================================

-- Variables
INSERT INTO variables (name, unit, source_per_body, native_resolution_m_per_body, nodata_value, in_index, notes, elevation_datum_per_body) VALUES (
  'latitude', 'grados',
  '{"moon": "Coordenada planetocéntrica de la grilla (LRO/LOLA, Marco IAU)", "mars": "Coordenada planetocéntrica de la grilla (MOLA, Marco IAU)", "earth": "Coordenada geográfica WGS 84"}'::jsonb,
  '{"moon": 1000, "mars": 1000, "earth": 1000}'::jsonb,
  NULL, TRUE,
  'Proxy de régimen de insolación y clave de la banda de muestreo.', NULL
) ON CONFLICT (name) DO UPDATE SET
  unit = EXCLUDED.unit, source_per_body = EXCLUDED.source_per_body,
  native_resolution_m_per_body = EXCLUDED.native_resolution_m_per_body,
  nodata_value = EXCLUDED.nodata_value, in_index = EXCLUDED.in_index,
  notes = EXCLUDED.notes, elevation_datum_per_body = EXCLUDED.elevation_datum_per_body;

INSERT INTO variables (name, unit, source_per_body, native_resolution_m_per_body, nodata_value, in_index, notes, elevation_datum_per_body) VALUES (
  'elevation', 'm',
  '{"moon": "LOLA (LRO) sobre la esfera de radio 1737.4 km", "mars": "MOLA, areoide MOLA", "earth": "Copernicus DEM GLO-90 (EGM2008). Se usa GLO-90 también fuera de Ecuador porque SRTM no cubre por encima de 60° (Isla Devon, Antártida)."}'::jsonb,
  '{"moon": 60, "mars": 463, "earth": 90}'::jsonb,
  NULL, TRUE,
  'Pendiente y rugosidad se recalculan sobre el DEM ya remuestreado a 1 km.', '{"moon": "Esfera de 1737.4 km", "mars": "Areoide MOLA", "earth": "Geoide EGM2008 (Copernicus DEM GLO-90)"}'::jsonb
) ON CONFLICT (name) DO UPDATE SET
  unit = EXCLUDED.unit, source_per_body = EXCLUDED.source_per_body,
  native_resolution_m_per_body = EXCLUDED.native_resolution_m_per_body,
  nodata_value = EXCLUDED.nodata_value, in_index = EXCLUDED.in_index,
  notes = EXCLUDED.notes, elevation_datum_per_body = EXCLUDED.elevation_datum_per_body;

INSERT INTO variables (name, unit, source_per_body, native_resolution_m_per_body, nodata_value, in_index, notes, elevation_datum_per_body) VALUES (
  'slope', 'grados',
  '{"moon": "Calculada sobre LOLA remuestreado a 1 km", "mars": "Calculada sobre MOLA remuestreado a 1 km", "earth": "Calculada sobre Copernicus DEM GLO-90 remuestreado a 1 km"}'::jsonb,
  '{"moon": 1000, "mars": 1000, "earth": 1000}'::jsonb,
  NULL, TRUE,
  'No interpolar un ráster de pendiente de otra resolución.', NULL
) ON CONFLICT (name) DO UPDATE SET
  unit = EXCLUDED.unit, source_per_body = EXCLUDED.source_per_body,
  native_resolution_m_per_body = EXCLUDED.native_resolution_m_per_body,
  nodata_value = EXCLUDED.nodata_value, in_index = EXCLUDED.in_index,
  notes = EXCLUDED.notes, elevation_datum_per_body = EXCLUDED.elevation_datum_per_body;

INSERT INTO variables (name, unit, source_per_body, native_resolution_m_per_body, nodata_value, in_index, notes, elevation_datum_per_body) VALUES (
  'roughness', 'm (TRI de Riley et al. 1999, ventana 3×3)',
  '{"moon": "TRI sobre LOLA remuestreado a 1 km", "mars": "TRI sobre MOLA remuestreado a 1 km", "earth": "TRI sobre Copernicus DEM GLO-90 remuestreado a 1 km"}'::jsonb,
  '{"moon": 1000, "mars": 1000, "earth": 1000}'::jsonb,
  NULL, TRUE,
  'Alternativa prevista: desviación estándar de la elevación en la misma ventana 3×3.', NULL
) ON CONFLICT (name) DO UPDATE SET
  unit = EXCLUDED.unit, source_per_body = EXCLUDED.source_per_body,
  native_resolution_m_per_body = EXCLUDED.native_resolution_m_per_body,
  nodata_value = EXCLUDED.nodata_value, in_index = EXCLUDED.in_index,
  notes = EXCLUDED.notes, elevation_datum_per_body = EXCLUDED.elevation_datum_per_body;

INSERT INTO variables (name, unit, source_per_body, native_resolution_m_per_body, nodata_value, in_index, notes, elevation_datum_per_body) VALUES (
  'albedo', 'adimensional (0–1)',
  '{"moon": "LROC WAC (pendiente de confirmación)", "mars": "TES / THEMIS (pendiente de confirmación)", "earth": "Landsat 8/9 o MODIS (pendiente de confirmación)"}'::jsonb,
  '{"moon": 100, "mars": 300, "earth": 30}'::jsonb,
  NULL, FALSE,
  'Fuera del índice hasta que Expertos confirme que la definición es comparable en los tres cuerpos. El pipeline está listo para incluirla (en_indice=true).', NULL
) ON CONFLICT (name) DO UPDATE SET
  unit = EXCLUDED.unit, source_per_body = EXCLUDED.source_per_body,
  native_resolution_m_per_body = EXCLUDED.native_resolution_m_per_body,
  nodata_value = EXCLUDED.nodata_value, in_index = EXCLUDED.in_index,
  notes = EXCLUDED.notes, elevation_datum_per_body = EXCLUDED.elevation_datum_per_body;

INSERT INTO variables (name, unit, source_per_body, native_resolution_m_per_body, nodata_value, in_index, notes, elevation_datum_per_body) VALUES (
  'thermal_inertia', 'J m⁻² K⁻¹ s⁻½',
  '{"moon": "Diviner (pendiente de confirmación)", "mars": "THEMIS / TES (pendiente de confirmación)", "earth": "Producto equivalente terrestre (pendiente de confirmación)"}'::jsonb,
  '{"moon": 200, "mars": 100, "earth": null}'::jsonb,
  NULL, FALSE,
  'Fuera del índice hasta que Expertos confirme comparabilidad. No hay variable meteorológica en el índice.', NULL
) ON CONFLICT (name) DO UPDATE SET
  unit = EXCLUDED.unit, source_per_body = EXCLUDED.source_per_body,
  native_resolution_m_per_body = EXCLUDED.native_resolution_m_per_body,
  nodata_value = EXCLUDED.nodata_value, in_index = EXCLUDED.in_index,
  notes = EXCLUDED.notes, elevation_datum_per_body = EXCLUDED.elevation_datum_per_body;

-- Parámetros de estandarización congelados
INSERT INTO std_params (body_ref, variable, center, scale, method, frozen_at) VALUES ('mars', 'latitude', 3.0637521223448276, 45.77510297951434, 'zscore', '2026-11-14T00:00:00Z') ON CONFLICT DO NOTHING;
INSERT INTO std_params (body_ref, variable, center, scale, method, frozen_at) VALUES ('mars', 'elevation', 751.1924440369046, 437.38319511352483, 'zscore', '2026-11-14T00:00:00Z') ON CONFLICT DO NOTHING;
INSERT INTO std_params (body_ref, variable, center, scale, method, frozen_at) VALUES ('mars', 'slope', 5.616859787900334, 2.4883427073487625, 'zscore', '2026-11-14T00:00:00Z') ON CONFLICT DO NOTHING;
INSERT INTO std_params (body_ref, variable, center, scale, method, frozen_at) VALUES ('mars', 'roughness', 128.6814689732111, 56.33350603762348, 'zscore', '2026-11-14T00:00:00Z') ON CONFLICT DO NOTHING;
INSERT INTO std_params (body_ref, variable, center, scale, method, frozen_at) VALUES ('moon', 'latitude', -1.9652744734576997, 45.86856673114371, 'zscore', '2026-11-14T00:00:00Z') ON CONFLICT DO NOTHING;
INSERT INTO std_params (body_ref, variable, center, scale, method, frozen_at) VALUES ('moon', 'elevation', 3046.1863776000996, 1364.6882279064196, 'zscore', '2026-11-14T00:00:00Z') ON CONFLICT DO NOTHING;
INSERT INTO std_params (body_ref, variable, center, scale, method, frozen_at) VALUES ('moon', 'slope', 13.919174505565639, 3.7035061257180075, 'zscore', '2026-11-14T00:00:00Z') ON CONFLICT DO NOTHING;
INSERT INTO std_params (body_ref, variable, center, scale, method, frozen_at) VALUES ('moon', 'roughness', 388.83195263351274, 97.96038212167221, 'zscore', '2026-11-14T00:00:00Z') ON CONFLICT DO NOTHING;

-- Firmas (Marte y Luna por separado)
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'ecuatorial', 'latitude', -0.5867467921542606, -5.488991817973853, 4.937985552492077, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'ecuatorial', 'elevation', 909.5010906573066, 671.1114382421515, 1150.4006929738957, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'ecuatorial', 'slope', 5.752195513316265, 3.907306619361857, 6.920239285399493, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'ecuatorial', 'roughness', 119.8885399986782, 96.45398552120722, 141.5808353804797, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'tropical', 'latitude', 10.795097091774934, -17.51949114007446, 17.958719859900995, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'tropical', 'elevation', 984.8942547492709, 718.1932721125481, 1235.6917266679502, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'tropical', 'slope', 5.430685762736378, 4.055120105341511, 6.454048023076054, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'tropical', 'roughness', 119.15348944019638, 92.70000125699816, 143.31012010879087, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'subtropical', 'latitude', -24.85215854253234, -28.967247588041342, 28.061584547270396, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'subtropical', 'elevation', 1079.2389154972093, 803.6960768130735, 1306.3229654102247, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'subtropical', 'slope', 4.514286763556026, 3.3019097640030233, 5.778671272670827, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'subtropical', 'roughness', 113.37508874963694, 92.3224302496504, 138.3904665736075, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'templada', 'latitude', 36.49905441566806, -41.16046898301032, 43.68063174473667, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'templada', 'elevation', 619.4185488573804, 391.22171319899985, 894.1457537622341, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'templada', 'slope', 6.006261097184105, 4.298424822585945, 7.292093844169484, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'templada', 'roughness', 143.18777515868936, 101.96240565480852, 177.1093873029617, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'templada_alta', 'latitude', 50.96184177445735, -57.79542800168539, 58.11276617912556, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'templada_alta', 'elevation', 312.8166735226626, 125.82648972708446, 453.2527458581029, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'templada_alta', 'slope', 3.69681686771031, 2.7557352086403353, 4.6066888357574785, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'templada_alta', 'roughness', 83.58472399386713, 60.50698671050719, 102.23930548276495, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'polar', 'latitude', 69.17202438521512, -77.17302902691608, 79.19603276265676, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'polar', 'elevation', 621.4466226599297, 382.8745281959061, 827.2517991363467, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'polar', 'slope', 8.38777909718421, 6.838350907903898, 10.247897731432754, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('mars', 'polar', 'roughness', 203.8455297150677, 158.98737416306034, 239.92463408772315, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'ecuatorial', 'latitude', 0.5095947804375677, -5.839987693808396, 6.049633033867933, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'ecuatorial', 'elevation', 4416.7074222684805, 3549.07372961115, 5032.148396664128, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'ecuatorial', 'slope', 12.962654101798869, 10.906809589267061, 14.912312708837167, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'ecuatorial', 'roughness', 367.61235543163565, 302.5133664894415, 416.722601581504, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'tropical', 'latitude', 11.41362518761283, -17.349670869578446, 17.311467473192003, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'tropical', 'elevation', 3984.6451699793315, 3327.8457342130346, 4787.407196062466, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'tropical', 'slope', 12.988867993997424, 10.974142842549998, 15.618854201213146, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'tropical', 'roughness', 380.8243301602414, 319.641801512202, 441.5772276300163, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'subtropical', 'latitude', 24.71212834139212, -29.64338040728731, 30.166293809242827, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'subtropical', 'elevation', 3512.1562055298646, 2682.393637796881, 4246.297178746914, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'subtropical', 'slope', 14.461444825548059, 11.746707670550848, 17.1191538523633, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'subtropical', 'roughness', 377.1551073527261, 309.72136127293385, 440.8510748608287, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'templada', 'latitude', -36.477695451975464, -43.659681120092536, 41.252769030757676, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'templada', 'elevation', 2628.6750506433423, 1902.7804507582869, 3147.8038432139497, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'templada', 'slope', 14.168947631968088, 11.546671790958946, 16.39568338291994, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'templada', 'roughness', 379.34804055567565, 331.4598668780521, 470.42204879328426, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'templada_alta', 'latitude', -52.41386205323228, -57.473351528854685, 55.8072766430584, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'templada_alta', 'elevation', 2004.9330986564066, 1407.0302144876848, 2472.3482795266623, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'templada_alta', 'slope', 14.017672298716114, 11.559329791907489, 16.526346001819206, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'templada_alta', 'roughness', 402.03299689940116, 325.7830837488623, 452.53311000239796, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'polar', 'latitude', -67.16789658254962, -80.11323847065746, 76.86591303074428, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'polar', 'elevation', 1840.8485928336245, 1264.396274709573, 2498.4925487548267, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'polar', 'slope', 15.20223203904092, 11.917309555334421, 17.462685851018627, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;
INSERT INTO signatures (body, lat_band, variable, median, q1, q3, n_cells) VALUES ('moon', 'polar', 'roughness', 431.3379321400837, 341.7196193515359, 509.4584621946717, 160) ON CONFLICT (body, lat_band, variable) DO UPDATE SET median = EXCLUDED.median, q1 = EXCLUDED.q1, q3 = EXCLUDED.q3, n_cells = EXCLUDED.n_cells;

-- Sitios de validación (PROVISIONALES, MOCK) y resultados
-- Desierto de Atacama (Yungay)
INSERT INTO validation_sites (id, name, lat, lon, geom, buffer_km, label, source, is_provisional, is_mock) VALUES (
  '373d738b-b1c4-595e-b6e0-5df3c74fee04', 'Desierto de Atacama (Yungay)', -24.08, -69.87,
  ST_SetSRID(ST_MakePoint(-69.87, -24.08), 4326),
  25, 'marciano', 'Literatura de análogos de Marte (lista provisional)', TRUE, TRUE
) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, lat = EXCLUDED.lat, lon = EXCLUDED.lon,
  geom = EXCLUDED.geom, buffer_km = EXCLUDED.buffer_km, label = EXCLUDED.label,
  source = EXCLUDED.source, is_provisional = EXCLUDED.is_provisional, is_mock = EXCLUDED.is_mock;
INSERT INTO validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at) VALUES (
  '373d738b-b1c4-595e-b6e0-5df3c74fee04', 0.7856, 0.0, 'marte', 'marte',
  'analog-delta-v1-superficie', '2026-11-14T00:00:00Z'
) ON CONFLICT (site_id) DO UPDATE SET delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at;

-- Valles secos de McMurdo
INSERT INTO validation_sites (id, name, lat, lon, geom, buffer_km, label, source, is_provisional, is_mock) VALUES (
  'd6c14b0d-7a8c-50ce-9a1a-983470916164', 'Valles secos de McMurdo', -77.45, 162.27,
  ST_SetSRID(ST_MakePoint(162.27, -77.45), 4326),
  30, 'marciano', 'Literatura de análogos de Marte (lista provisional)', TRUE, TRUE
) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, lat = EXCLUDED.lat, lon = EXCLUDED.lon,
  geom = EXCLUDED.geom, buffer_km = EXCLUDED.buffer_km, label = EXCLUDED.label,
  source = EXCLUDED.source, is_provisional = EXCLUDED.is_provisional, is_mock = EXCLUDED.is_mock;
INSERT INTO validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at) VALUES (
  'd6c14b0d-7a8c-50ce-9a1a-983470916164', 0.1304, 0.1892, 'luna', 'marte',
  'analog-delta-v1-superficie', '2026-11-14T00:00:00Z'
) ON CONFLICT (site_id) DO UPDATE SET delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at;

-- Isla Devon (cráter Haughton)
INSERT INTO validation_sites (id, name, lat, lon, geom, buffer_km, label, source, is_provisional, is_mock) VALUES (
  '3b62ee53-cf71-58ee-931c-012981487551', 'Isla Devon (cráter Haughton)', 75.38, -89.72,
  ST_SetSRID(ST_MakePoint(-89.72, 75.38), 4326),
  20, 'ambos', 'Estación de investigación de análogos (lista provisional)', TRUE, TRUE
) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, lat = EXCLUDED.lat, lon = EXCLUDED.lon,
  geom = EXCLUDED.geom, buffer_km = EXCLUDED.buffer_km, label = EXCLUDED.label,
  source = EXCLUDED.source, is_provisional = EXCLUDED.is_provisional, is_mock = EXCLUDED.is_mock;
INSERT INTO validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at) VALUES (
  '3b62ee53-cf71-58ee-931c-012981487551', 0.4567, 0.1304, 'ambos', 'ambos',
  'analog-delta-v1-superficie', '2026-11-14T00:00:00Z'
) ON CONFLICT (site_id) DO UPDATE SET delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at;

-- Río Tinto
INSERT INTO validation_sites (id, name, lat, lon, geom, buffer_km, label, source, is_provisional, is_mock) VALUES (
  'cf6c1981-2bda-53f1-8cb6-6c2ad3632caf', 'Río Tinto', 37.7, -6.6,
  ST_SetSRID(ST_MakePoint(-6.6, 37.7), 4326),
  15, 'marciano', 'Literatura de análogos de Marte (lista provisional)', TRUE, TRUE
) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, lat = EXCLUDED.lat, lon = EXCLUDED.lon,
  geom = EXCLUDED.geom, buffer_km = EXCLUDED.buffer_km, label = EXCLUDED.label,
  source = EXCLUDED.source, is_provisional = EXCLUDED.is_provisional, is_mock = EXCLUDED.is_mock;
INSERT INTO validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at) VALUES (
  'cf6c1981-2bda-53f1-8cb6-6c2ad3632caf', 0.7646, 0.0, 'marte', 'marte',
  'analog-delta-v1-superficie', '2026-11-14T00:00:00Z'
) ON CONFLICT (site_id) DO UPDATE SET delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at;

-- Desierto de Mojave
INSERT INTO validation_sites (id, name, lat, lon, geom, buffer_km, label, source, is_provisional, is_mock) VALUES (
  'a69c3149-725e-55c6-9f51-b4be78ac28bb', 'Desierto de Mojave', 35.05, -115.9,
  ST_SetSRID(ST_MakePoint(-115.9, 35.05), 4326),
  25, 'marciano', 'Literatura de análogos de Marte (lista provisional)', TRUE, TRUE
) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, lat = EXCLUDED.lat, lon = EXCLUDED.lon,
  geom = EXCLUDED.geom, buffer_km = EXCLUDED.buffer_km, label = EXCLUDED.label,
  source = EXCLUDED.source, is_provisional = EXCLUDED.is_provisional, is_mock = EXCLUDED.is_mock;
INSERT INTO validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at) VALUES (
  'a69c3149-725e-55c6-9f51-b4be78ac28bb', 0.7143, 0.0, 'marte', 'marte',
  'analog-delta-v1-superficie', '2026-11-14T00:00:00Z'
) ON CONFLICT (site_id) DO UPDATE SET delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at;

-- Cráter Barringer
INSERT INTO validation_sites (id, name, lat, lon, geom, buffer_km, label, source, is_provisional, is_mock) VALUES (
  '603e7e8d-066f-597e-a660-a78fb61aa182', 'Cráter Barringer', 35.027, -111.023,
  ST_SetSRID(ST_MakePoint(-111.023, 35.027), 4326),
  5, 'lunar', 'Literatura de análogos lunares (lista provisional)', TRUE, TRUE
) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, lat = EXCLUDED.lat, lon = EXCLUDED.lon,
  geom = EXCLUDED.geom, buffer_km = EXCLUDED.buffer_km, label = EXCLUDED.label,
  source = EXCLUDED.source, is_provisional = EXCLUDED.is_provisional, is_mock = EXCLUDED.is_mock;
INSERT INTO validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at) VALUES (
  '603e7e8d-066f-597e-a660-a78fb61aa182', 0.0, 0.6161, 'luna', 'luna',
  'analog-delta-v1-superficie', '2026-11-14T00:00:00Z'
) ON CONFLICT (site_id) DO UPDATE SET delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at;

-- Teide (Tenerife)
INSERT INTO validation_sites (id, name, lat, lon, geom, buffer_km, label, source, is_provisional, is_mock) VALUES (
  'cbb10b4a-716f-539f-a3aa-578a3ed0a29c', 'Teide (Tenerife)', 28.27, -16.64,
  ST_SetSRID(ST_MakePoint(-16.64, 28.27), 4326),
  15, 'lunar', 'Literatura de análogos lunares (lista provisional)', TRUE, TRUE
) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, lat = EXCLUDED.lat, lon = EXCLUDED.lon,
  geom = EXCLUDED.geom, buffer_km = EXCLUDED.buffer_km, label = EXCLUDED.label,
  source = EXCLUDED.source, is_provisional = EXCLUDED.is_provisional, is_mock = EXCLUDED.is_mock;
INSERT INTO validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at) VALUES (
  'cbb10b4a-716f-539f-a3aa-578a3ed0a29c', 0.0, 0.8872, 'luna', 'luna',
  'analog-delta-v1-superficie', '2026-11-14T00:00:00Z'
) ON CONFLICT (site_id) DO UPDATE SET delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at;

-- Campo volcánico de San Francisco (Flagstaff)
INSERT INTO validation_sites (id, name, lat, lon, geom, buffer_km, label, source, is_provisional, is_mock) VALUES (
  '6a712c03-0a85-56d8-93be-d1be2719949b', 'Campo volcánico de San Francisco (Flagstaff)', 35.35, -111.68,
  ST_SetSRID(ST_MakePoint(-111.68, 35.35), 4326),
  15, 'lunar', 'Literatura de análogos lunares (lista provisional)', TRUE, TRUE
) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, lat = EXCLUDED.lat, lon = EXCLUDED.lon,
  geom = EXCLUDED.geom, buffer_km = EXCLUDED.buffer_km, label = EXCLUDED.label,
  source = EXCLUDED.source, is_provisional = EXCLUDED.is_provisional, is_mock = EXCLUDED.is_mock;
INSERT INTO validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at) VALUES (
  '6a712c03-0a85-56d8-93be-d1be2719949b', 0.0, 0.599, 'luna', 'luna',
  'analog-delta-v1-superficie', '2026-11-14T00:00:00Z'
) ON CONFLICT (site_id) DO UPDATE SET delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at;

-- Yasuní (Amazonía ecuatoriana)
INSERT INTO validation_sites (id, name, lat, lon, geom, buffer_km, label, source, is_provisional, is_mock) VALUES (
  '4c938dbf-703b-599e-a1aa-6245331b06d6', 'Yasuní (Amazonía ecuatoriana)', -0.7, -76.4,
  ST_SetSRID(ST_MakePoint(-76.4, -0.7), 4326),
  20, 'no_analogo', 'Contraste tropical húmedo (lista provisional)', TRUE, TRUE
) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, lat = EXCLUDED.lat, lon = EXCLUDED.lon,
  geom = EXCLUDED.geom, buffer_km = EXCLUDED.buffer_km, label = EXCLUDED.label,
  source = EXCLUDED.source, is_provisional = EXCLUDED.is_provisional, is_mock = EXCLUDED.is_mock;
INSERT INTO validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at) VALUES (
  '4c938dbf-703b-599e-a1aa-6245331b06d6', 0.0, 0.0, 'ninguno', 'ninguno',
  'analog-delta-v1-superficie', '2026-11-14T00:00:00Z'
) ON CONFLICT (site_id) DO UPDATE SET delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at;

-- Llanura de los Países Bajos
INSERT INTO validation_sites (id, name, lat, lon, geom, buffer_km, label, source, is_provisional, is_mock) VALUES (
  '344a37dc-07f0-5704-aae5-2a2325de2aa9', 'Llanura de los Países Bajos', 52.3, 5.3,
  ST_SetSRID(ST_MakePoint(5.3, 52.3), 4326),
  20, 'no_analogo', 'Contraste de baja pendiente (lista provisional)', TRUE, TRUE
) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, lat = EXCLUDED.lat, lon = EXCLUDED.lon,
  geom = EXCLUDED.geom, buffer_km = EXCLUDED.buffer_km, label = EXCLUDED.label,
  source = EXCLUDED.source, is_provisional = EXCLUDED.is_provisional, is_mock = EXCLUDED.is_mock;
INSERT INTO validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at) VALUES (
  '344a37dc-07f0-5704-aae5-2a2325de2aa9', 0.2092, 0.0, 'ninguno', 'ninguno',
  'analog-delta-v1-superficie', '2026-11-14T00:00:00Z'
) ON CONFLICT (site_id) DO UPDATE SET delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at;

-- Umbrales congelados
INSERT INTO thresholds (body, value, metric, d_max, sensitivity, precision, auc, frozen_at) VALUES ('mars', 0.45668725123328635, 'youden', 1.8752061968910816, 0.8, 1.0, 0.9600000000000001, '2026-11-14T00:00:00Z') ON CONFLICT DO NOTHING;
INSERT INTO thresholds (body, value, metric, d_max, sensitivity, precision, auc, frozen_at) VALUES ('moon', 0.13043478260869557, 'youden', 2.4296228304703944, 1.0, 0.8, 0.9583333333333334, '2026-11-14T00:00:00Z') ON CONFLICT DO NOTHING;

-- Zonas prioritarias de Ecuador (recuento reducido; el ráster completo está en ecuador_rasters)
INSERT INTO ecuador_results (lat, lon, geom, delta_mars, delta_moon, class, valid_mask, name, is_priority) VALUES (
  -3.995, -77.915, ST_SetSRID(ST_MakePoint(-77.915, -3.995), 4326),
  0.7419, 0.0, 'marte', TRUE, 'Faldas orientales (Zamora-Chinchipe)', TRUE
);
INSERT INTO cells (body, lat, lon, geom, elevation_m, slope_deg, roughness_tri, valid_mask) VALUES (
  'earth', -3.995, -77.915, ST_SetSRID(ST_MakePoint(-77.915, -3.995), 4326),
  845.0, 3.99, 150.42, TRUE
) ON CONFLICT (body, lat, lon) DO UPDATE SET elevation_m = EXCLUDED.elevation_m,
  slope_deg = EXCLUDED.slope_deg, roughness_tri = EXCLUDED.roughness_tri;
INSERT INTO ecuador_results (lat, lon, geom, delta_mars, delta_moon, class, valid_mask, name, is_priority) VALUES (
  -0.54, -78.37, ST_SetSRID(ST_MakePoint(-78.37, -0.54), 4326),
  0.0, 0.6758, 'luna', TRUE, 'Sincholagua', TRUE
);
INSERT INTO cells (body, lat, lon, geom, elevation_m, slope_deg, roughness_tri, valid_mask) VALUES (
  'earth', -0.54, -78.37, ST_SetSRID(ST_MakePoint(-78.37, -0.54), 4326),
  3155.0, 10.08, 434.97, TRUE
) ON CONFLICT (body, lat, lon) DO UPDATE SET elevation_m = EXCLUDED.elevation_m,
  slope_deg = EXCLUDED.slope_deg, roughness_tri = EXCLUDED.roughness_tri;
INSERT INTO ecuador_results (lat, lon, geom, delta_mars, delta_moon, class, valid_mask, name, is_priority) VALUES (
  -1.47, -78.82, ST_SetSRID(ST_MakePoint(-78.82, -1.47), 4326),
  0.0, 0.6385, 'luna', TRUE, 'Chimborazo (arenal y páramo)', TRUE
);
INSERT INTO cells (body, lat, lon, geom, elevation_m, slope_deg, roughness_tri, valid_mask) VALUES (
  'earth', -1.47, -78.82, ST_SetSRID(ST_MakePoint(-78.82, -1.47), 4326),
  4026.0, 7.93, 373.64, TRUE
) ON CONFLICT (body, lat, lon) DO UPDATE SET elevation_m = EXCLUDED.elevation_m,
  slope_deg = EXCLUDED.slope_deg, roughness_tri = EXCLUDED.roughness_tri;
INSERT INTO ecuador_results (lat, lon, geom, delta_mars, delta_moon, class, valid_mask, name, is_priority) VALUES (
  -1.67, -78.41, ST_SetSRID(ST_MakePoint(-78.41, -1.67), 4326),
  0.0, 0.5982, 'luna', TRUE, 'El Altar', TRUE
);
INSERT INTO cells (body, lat, lon, geom, elevation_m, slope_deg, roughness_tri, valid_mask) VALUES (
  'earth', -1.67, -78.41, ST_SetSRID(ST_MakePoint(-78.41, -1.67), 4326),
  3182.0, 8.12, 358.87, TRUE
) ON CONFLICT (body, lat, lon) DO UPDATE SET elevation_m = EXCLUDED.elevation_m,
  slope_deg = EXCLUDED.slope_deg, roughness_tri = EXCLUDED.roughness_tri;
INSERT INTO ecuador_results (lat, lon, geom, delta_mars, delta_moon, class, valid_mask, name, is_priority) VALUES (
  0.03, -77.99, ST_SetSRID(ST_MakePoint(-77.99, 0.03), 4326),
  0.0, 0.5914, 'luna', TRUE, 'Cayambe', TRUE
);
INSERT INTO cells (body, lat, lon, geom, elevation_m, slope_deg, roughness_tri, valid_mask) VALUES (
  'earth', 0.03, -77.99, ST_SetSRID(ST_MakePoint(-77.99, 0.03), 4326),
  3129.0, 8.11, 379.58, TRUE
) ON CONFLICT (body, lat, lon) DO UPDATE SET elevation_m = EXCLUDED.elevation_m,
  slope_deg = EXCLUDED.slope_deg, roughness_tri = EXCLUDED.roughness_tri;
INSERT INTO ecuador_results (lat, lon, geom, delta_mars, delta_moon, class, valid_mask, name, is_priority) VALUES (
  -0.48, -78.14, ST_SetSRID(ST_MakePoint(-78.14, -0.48), 4326),
  0.0, 0.5052, 'luna', TRUE, 'Antisana', TRUE
);
INSERT INTO cells (body, lat, lon, geom, elevation_m, slope_deg, roughness_tri, valid_mask) VALUES (
  'earth', -0.48, -78.14, ST_SetSRID(ST_MakePoint(-78.14, -0.48), 4326),
  5045.0, 6.8, 286.01, TRUE
) ON CONFLICT (body, lat, lon) DO UPDATE SET elevation_m = EXCLUDED.elevation_m,
  slope_deg = EXCLUDED.slope_deg, roughness_tri = EXCLUDED.roughness_tri;
INSERT INTO ecuador_results (lat, lon, geom, delta_mars, delta_moon, class, valid_mask, name, is_priority) VALUES (
  -0.68, -78.44, ST_SetSRID(ST_MakePoint(-78.44, -0.68), 4326),
  0.0, 0.4614, 'luna', TRUE, 'Cotopaxi (páramo)', TRUE
);
INSERT INTO cells (body, lat, lon, geom, elevation_m, slope_deg, roughness_tri, valid_mask) VALUES (
  'earth', -0.68, -78.44, ST_SetSRID(ST_MakePoint(-78.44, -0.68), 4326),
  3040.0, 6.4, 378.51, TRUE
) ON CONFLICT (body, lat, lon) DO UPDATE SET elevation_m = EXCLUDED.elevation_m,
  slope_deg = EXCLUDED.slope_deg, roughness_tri = EXCLUDED.roughness_tri;
INSERT INTO ecuador_results (lat, lon, geom, delta_mars, delta_moon, class, valid_mask, name, is_priority) VALUES (
  -0.85, -78.9, ST_SetSRID(ST_MakePoint(-78.9, -0.85), 4326),
  0.0, 0.3801, 'luna', TRUE, 'Quilotoa', TRUE
);
INSERT INTO cells (body, lat, lon, geom, elevation_m, slope_deg, roughness_tri, valid_mask) VALUES (
  'earth', -0.85, -78.9, ST_SetSRID(ST_MakePoint(-78.9, -0.85), 4326),
  4003.0, 5.15, 280.36, TRUE
) ON CONFLICT (body, lat, lon) DO UPDATE SET elevation_m = EXCLUDED.elevation_m,
  slope_deg = EXCLUDED.slope_deg, roughness_tri = EXCLUDED.roughness_tri;
INSERT INTO ecuador_results (lat, lon, geom, delta_mars, delta_moon, class, valid_mask, name, is_priority) VALUES (
  -0.37, -91.55, ST_SetSRID(ST_MakePoint(-91.55, -0.37), 4326),
  0.0, 0.0, 'ninguno', TRUE, 'Fernandina (Galápagos)', TRUE
);
INSERT INTO cells (body, lat, lon, geom, elevation_m, slope_deg, roughness_tri, valid_mask) VALUES (
  'earth', -0.37, -91.55, ST_SetSRID(ST_MakePoint(-91.55, -0.37), 4326),
  2067.0, 1.66, 102.54, TRUE
) ON CONFLICT (body, lat, lon) DO UPDATE SET elevation_m = EXCLUDED.elevation_m,
  slope_deg = EXCLUDED.slope_deg, roughness_tri = EXCLUDED.roughness_tri;

-- Referencias a rásteres MOCK (sitio estático)
INSERT INTO ecuador_rasters (layer, path, kind, resolucion_m, west, north, east, south, nodata, label, in_index, frozen_at) VALUES (
  'delta_marte', '/mock/delta_marte.png', 'similitud', 1110, -92.2, 1.6, -75.0, -5.1,
  NULL, NULL, TRUE, '2026-11-14T00:00:00Z'
) ON CONFLICT (layer) DO UPDATE SET path = EXCLUDED.path, kind = EXCLUDED.kind,
  west = EXCLUDED.west, north = EXCLUDED.north, east = EXCLUDED.east, south = EXCLUDED.south,
  label = EXCLUDED.label, in_index = EXCLUDED.in_index, frozen_at = EXCLUDED.frozen_at;
INSERT INTO ecuador_rasters (layer, path, kind, resolucion_m, west, north, east, south, nodata, label, in_index, frozen_at) VALUES (
  'delta_luna', '/mock/delta_luna.png', 'similitud', 1110, -92.2, 1.6, -75.0, -5.1,
  NULL, NULL, TRUE, '2026-11-14T00:00:00Z'
) ON CONFLICT (layer) DO UPDATE SET path = EXCLUDED.path, kind = EXCLUDED.kind,
  west = EXCLUDED.west, north = EXCLUDED.north, east = EXCLUDED.east, south = EXCLUDED.south,
  label = EXCLUDED.label, in_index = EXCLUDED.in_index, frozen_at = EXCLUDED.frozen_at;
INSERT INTO ecuador_rasters (layer, path, kind, resolucion_m, west, north, east, south, nodata, label, in_index, frozen_at) VALUES (
  'clases', '/mock/clases.png', 'clase', 1110, -92.2, 1.6, -75.0, -5.1,
  NULL, NULL, TRUE, '2026-11-14T00:00:00Z'
) ON CONFLICT (layer) DO UPDATE SET path = EXCLUDED.path, kind = EXCLUDED.kind,
  west = EXCLUDED.west, north = EXCLUDED.north, east = EXCLUDED.east, south = EXCLUDED.south,
  label = EXCLUDED.label, in_index = EXCLUDED.in_index, frozen_at = EXCLUDED.frozen_at;
INSERT INTO ecuador_rasters (layer, path, kind, resolucion_m, west, north, east, south, nodata, label, in_index, frozen_at) VALUES (
  'clima', '/mock/clima.png', 'interpretacion', 1110, -92.2, 1.6, -75.0, -5.1,
  NULL, 'Interpretación, no entra al índice', FALSE, '2026-11-14T00:00:00Z'
) ON CONFLICT (layer) DO UPDATE SET path = EXCLUDED.path, kind = EXCLUDED.kind,
  west = EXCLUDED.west, north = EXCLUDED.north, east = EXCLUDED.east, south = EXCLUDED.south,
  label = EXCLUDED.label, in_index = EXCLUDED.in_index, frozen_at = EXCLUDED.frozen_at;
